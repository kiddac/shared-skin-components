
from enigma import ePixmap  # , ePicLoad
from Components.Harddisk import harddiskmanager
from Components.Renderer.Renderer import Renderer
from ServiceReference import ServiceReference
from Tools.Alternatives import GetWithAlternative
from Tools.Directories import SCOPE_CURRENT_SKIN, resolveFilename
from PIL import Image, ImageFile, PngImagePlugin
from unicodedata import normalize

import glob
import os
import re
import string
import sys

_simple_palette = re.compile(b"^\xff*\x00\xff*$")

pythonVer = 2
if sys.version_info.major == 3:
    pythonVer = 3

if pythonVer == 3:
    unicode = str


searchPaths = []
lastPiconPath = None

# create temporary directory
if not os.path.exists("/tmp/temppicons"):
    os.makedirs("/tmp/temppicons")


# png code courtest of adw on stackoverflow
def patched_chunk_tRNS(self, pos, len):
    i16 = PngImagePlugin.i16
    s = ImageFile._safe_read(self.fp, len)
    if self.im_mode == "P":
        i = string.find(s, chr(0))
        if i >= 0:
            self.im_info["transparency"] = map(ord, s)
    elif self.im_mode == "L":
        self.im_info["transparency"] = i16(s)
    elif self.im_mode == "RGB":
        self.im_info["transparency"] = (i16(s), i16(s[2:]), i16(s[4:]))
    return s


# png code courtest of adw on stackoverflow
def patched_load(self):
    if self.im and self.palette and self.palette.dirty:
        self.im.putpalette(*self.palette.getdata())
        self.palette.dirty = 0
        self.palette.rawmode = None
        try:
            trans = self.info["transparency"]
        except KeyError:
            self.palette.mode = "RGB"
        else:
            try:
                for i, a in enumerate(trans):
                    self.im.putpalettealpha(i, a)
            except TypeError:
                self.im.putpalettealpha(trans, 0)
            self.palette.mode = "RGBA"
    if self.im:
        return self.im.pixel_access(self.readonly)


def mycall(self, cid, pos, length):
    if cid.decode("ascii") == "tRNS":
        return self.chunk_TRNS(pos, length)
    else:
        return getattr(self, "chunk_" + cid.decode("ascii"))(pos, length)


def mychunk_TRNS(self, pos, length):
    i16 = PngImagePlugin.i16
    s = ImageFile._safe_read(self.fp, length)
    if self.im_mode == "P":
        if _simple_palette.match(s):
            i = s.find(b"\0")
            if i >= 0:
                self.im_info["transparency"] = i
        else:
            self.im_info["transparency"] = s
    elif self.im_mode in ("1", "L", "I"):
        self.im_info["transparency"] = i16(s)
    elif self.im_mode == "RGB":
        self.im_info["transparency"] = i16(s), i16(s, 2), i16(s, 4)
    return s


if pythonVer == 2:
    Image.Image.load = patched_load
    PngImagePlugin.PngStream.chunk_tRNS = patched_chunk_tRNS
else:
    PngImagePlugin.ChunkStream.call = mycall
    PngImagePlugin.PngStream.chunk_TRNS = mychunk_TRNS


def initPiconPaths():
    global searchPaths
    searchPaths = []
    for mp in ("/usr/share/enigma2/", "/"):
        onMountpointAdded(mp)
    for part in harddiskmanager.getMountedPartitions():
        mp = os.path.join(part.mountpoint, "usr/share/enigma2")
        onMountpointAdded(part.mountpoint)
        onMountpointAdded(mp)


def onMountpointAdded(mountpoint):
    global searchPaths
    try:
        path = os.path.join(mountpoint, "XPicons", "")
        if os.path.isdir(path) and path not in searchPaths:
            for fn in os.listdir(path):
                if fn.endswith(".png"):
                    print("[Picon] adding path:", path)
                    searchPaths.append(path)
                    break
    except Exception as ex:
        print("[Picon] Failed to investigate %s:" % mountpoint, ex)


def onMountpointRemoved(mountpoint):
    global searchPaths
    path = os.path.join(mountpoint, "XPicons", "")
    try:
        searchPaths.remove(path)
        print("[Picon] removed path:", path)
    except:
        pass


def onPartitionChange(why, part):
    if why == "add":
        onMountpointAdded(part.mountpoint)
    elif why == "remove":
        onMountpointRemoved(part.mountpoint)


def findPicon(serviceName):
    global lastPiconPath
    if lastPiconPath is not None:
        pngname = lastPiconPath + serviceName + ".png"
        return pngname if os.path.exists(pngname) else ""
    else:
        global searchPaths
        pngname = ""
        for path in searchPaths:
            if os.path.exists(path) and not path.startswith("/media/net"):
                pngname = path + serviceName + ".png"
                if os.path.exists(pngname):
                    lastPiconPath = path
                    return pngname
        return ""


def getPiconName(serviceName):
    fields = GetWithAlternative(serviceName).split(":", 10)[:10]  # Remove the path and name fields, and replace ":" by "_"
    if not fields or len(fields) < 10:
        return ""
    pngname = findPicon("_".join(fields))
    if not pngname and not fields[6].endswith("0000"):
        fields[6] = fields[6][:-4] + "0000"  # Remove "sub-network" from namespace
        pngname = findPicon("_".join(fields))
    if not pngname and fields[0] != "1":
        fields[0] = "1"  # Fallback to 1 for other reftypes
        pngname = findPicon("_".join(fields))
    if not pngname and fields[2] != "1":
        fields[2] = "1"  # Fallback to 1 for services with different service types
        pngname = findPicon("_".join(fields))
    if not pngname:
        name = ServiceReference(serviceName).getServiceName()  # Picon by channel name

        if pythonVer == 2:
            name = normalize("NFKD", unicode(name, "utf_8", errors="ignore")).encode("ASCII", "ignore")
        elif pythonVer == 3:
            name = normalize("NFKD", name).encode("ASCII", "ignore").decode()

        name = re.sub("[^a-z0-9]", "", name.replace("&", "and").replace("+", "plus").replace("*", "star").lower())
        if name:
            pngname = findPicon(name)
            if not pngname:
                name = re.sub("(fhd|uhd|hd|sd|4k)$", "", name)
                if name:
                    pngname = findPicon(name)
    return pngname


class Slyk18XPicon(Renderer):
    GUI_WIDGET = ePixmap

    def __init__(self):
        Renderer.__init__(self)
        # self.PicLoad = ePicLoad()
        # self.PicLoad.PictureData.get().append(self.updatePicon)
        self.piconsize = (0, 0)
        self.pngname = ""
        self.lastPath = None

        self.defaultpngname = resolveFilename(SCOPE_CURRENT_SKIN, "picon_default.png")
            
    def addPath(self, value):
        if os.path.exists(value):
            global searchPaths
            value = os.path.join(value, "")
            if value not in searchPaths:
                searchPaths.append(value)

    def applySkin(self, desktop, parent):
        attribs = self.skinAttributes[:]
        for (attrib, value) in self.skinAttributes:
            if attrib == "path":
                self.addPath(value)
                attribs.remove((attrib, value))
            elif attrib == "size":
                self.piconsize = value
        self.skinAttributes = attribs
        return Renderer.applySkin(self, desktop, parent)

    def postWidgetCreate(self, instance):
        self.changed((self.CHANGED_DEFAULT,))

    # def updatePicon(self, picInfo=None):
    #    ptr = self.PicLoad.getData()
    #     if ptr is not None:
    #       self.instance.setPixmap(ptr.__deref__())
    #        self.instance.show()

    def changed(self, what):
        if self.instance:
            pngname = ""
            if what[0] == 1 or what[0] == 3:
                pngname = getPiconName(self.source.text)

                if pngname:
                    tempname = pngname.replace(lastPiconPath, "")
                if not os.path.exists(pngname):  # no picon for service found
                    pngname = self.defaultpngname

                if self.pngname != pngname:
                    if pngname:

                        try:
                            if pngname != self.defaultpngname:
                                try:
                                    Image.open(pngname).convert("RGBA").resize((self.piconsize), Image.Resampling.LANCZOS).save("/tmp/temppicons/" + str(tempname), "PNG")
                                except:
                                    Image.open(pngname).convert("RGBA").resize((self.piconsize), Image.ANTIALIAS).save("/tmp/temppicons/" + str(tempname), "PNG")
                                self.instance.setScale(1)
                                self.instance.setPixmapFromFile("/tmp/temppicons/" + str(tempname))
                                self.instance.show()
                            elif pngname == self.defaultpngname:
                                try:
                                    Image.open(pngname).convert("RGBA").resize((self.piconsize), Image.Resampling.LANCZOS).save("/tmp/temppicons/" + "picon_default.png", "PNG")
                                except:
                                    Image.open(pngname).convert("RGBA").resize((self.piconsize), Image.ANTIALIAS).save("/tmp/temppicons/" + "picon_default.png", "PNG")
                                self.instance.setScale(1)
                                self.instance.setPixmapFromFile("/tmp/temppicons/picon_default.png")
                                self.instance.show()

                        except Exception as e:
                            print(e)
                            print("[Picon] Bad picon file?: %s" % pngname)
                            return

                    else:
                        self.instance.hide()
                    self.pngname = pngname

                    self.pngname = pngname
                    # delete any existing pngs
                    if os.path.exists("/tmp/temppicons"):
                        for filename in glob.glob("/tmp/temppicons/*.png"):
                            os.remove(filename)
            elif what[0] == 2:
                self.pngname = ""
                self.instance.hide()


harddiskmanager.on_partition_list_change.append(onPartitionChange)
initPiconPaths()
