from __future__ import absolute_import

from Components.Harddisk import harddiskmanager
from Components.Renderer.Renderer import Renderer
from enigma import ePixmap, ePicLoad
from ServiceReference import ServiceReference
from PIL import Image, ImageFile, PngImagePlugin
from Tools.Alternatives import GetWithAlternative
from Tools.Directories import pathExists, SCOPE_ACTIVE_SKIN, resolveFilename

import string
import glob
import sys
import os
import re
import unicodedata

_simple_palette = re.compile(b"^\xff*\x00\xff*$")

pythonVer = 2
if sys.version_info.major == 3:
    pythonVer = 3


searchPaths = []
lastPiconPath = None

# create temporary directory
if not os.path.exists("/tmp/temppicons"):
    os.makedirs("/tmp/temppicons")


# png code courtest of adw on stackoverflow
def patched_chunk_tRNS(self, pos, len):
    i16 = PngImagePlugin.i16
    s = ImageFile._safe_read(self.fp, len)
    if self.im_mode == 'P':
        i = string.find(s, chr(0))
        if i >= 0:
            self.im_info["transparency"] = map(ord, s)
    elif self.im_mode == 'L':
        self.im_info['transparency'] = i16(s)
    elif self.im_mode == 'RGB':
        self.im_info['transparency'] = (i16(s), i16(s[2:]), i16(s[4:]))
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
    for mp in ('/usr/share/enigma2/', '/'):
        onMountpointAdded(mp)
    for part in harddiskmanager.getMountedPartitions():
        onMountpointAdded(part.mountpoint)


def onMountpointAdded(mountpoint):
    global searchPaths
    try:
        path = os.path.join(mountpoint, 'picon') + '/'
        if os.path.isdir(path) and path not in searchPaths:
            for fn in os.listdir(path):
                if fn.endswith('.png'):
                    print("[Picon] adding path:", path)
                    searchPaths.append(path)
                    break
    except Exception as ex:
        print("[Picon] Failed to investigate %s:" % mountpoint, ex)


def onMountpointRemoved(mountpoint):
    global searchPaths
    path = os.path.join(mountpoint, 'picon') + '/'
    try:
        searchPaths.remove(path)
        print("[Picon] removed path:", path)
    except:
        pass


def onPartitionChange(why, part):
    if why == 'add':
        onMountpointAdded(part.mountpoint)
    elif why == 'remove':
        onMountpointRemoved(part.mountpoint)


def findPicon(serviceName):
    global lastPiconPath
    if lastPiconPath is not None:
        pngname = lastPiconPath + serviceName + ".png"
        if pathExists(pngname):
            return pngname
        else:
            return ""
    else:
        global searchPaths
        pngname = ""
        for path in searchPaths:
            if pathExists(path) and not path.startswith('/media/net') and not path.startswith('/media/autofs'):
                pngname = path + serviceName + ".png"
                if pathExists(pngname):
                    lastPiconPath = path
                    break
            elif pathExists(path):
                pngname = path + serviceName + ".png"
                if pathExists(pngname):
                    lastPiconPath = path
                    break
        if pathExists(pngname):
            return pngname
        else:
            return ""


def getPiconName(serviceName):
    # remove the path and name fields, and replace ':' by '_'
    fields = GetWithAlternative(serviceName).split(':', 10)[:10]
    if not fields or len(fields) < 10:
        return ""
    pngname = findPicon('_'.join(fields))
    if not pngname and not fields[6].endswith("0000"):
        # remove "sub-network" from namespace
        fields[6] = fields[6][:-4] + "0000"
        pngname = findPicon('_'.join(fields))
    if not pngname and fields[0] != '1':
        # fallback to 1 for IPTV streams
        fields[0] = '1'
        pngname = findPicon('_'.join(fields))
    if not pngname and fields[2] != '2':
        # fallback to 1 for TV services with non-standard service types
        fields[2] = '1'
        pngname = findPicon('_'.join(fields))
    if not pngname:  # picon by channel name
        name = ServiceReference(serviceName).getServiceName()

        if pythonVer == 2:
            name = unicodedata.normalize('NFKD', unicode(name, 'utf_8', errors='ignore')).encode('ASCII', 'ignore')
        elif pythonVer == 3:
            name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ascii')

        name = re.sub('[^a-z0-9]', '', name.replace('&', 'and').replace('+', 'plus').replace('*', 'star').lower())
        if len(name) > 0:
            pngname = findPicon(name)
            if not pngname and len(name) > 2 and name.endswith('hd'):
                pngname = findPicon(name[:-2])
    return pngname


class Slyk18Picon(Renderer):
    def __init__(self):
        Renderer.__init__(self)
        self.PicLoad = ePicLoad()
        self.PicLoad.PictureData.get().append(self.updatePicon)
        self.piconsize = (0, 0)
        self.pngname = ""
        self.lastPath = None
        pngname = findPicon("picon_default")
        self.defaultpngname = resolveFilename(SCOPE_ACTIVE_SKIN, "picon_default.png")

    def addPath(self, value):
        if pathExists(value):
            global searchPaths
            if not value.endswith('/'):
                value += '/'
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

    GUI_WIDGET = ePixmap

    def postWidgetCreate(self, instance):
        self.changed((self.CHANGED_DEFAULT,))

    def updatePicon(self, picInfo=None):
        ptr = self.PicLoad.getData()
        if ptr is not None:
            self.instance.setPixmap(ptr.__deref__())
            self.instance.show()

    def changed(self, what):
        if self.instance:
            pngname = ""
            if what[0] == 1 or what[0] == 3:
                pngname = getPiconName(self.source.text)
                if pngname:
                    tempname = pngname.replace(lastPiconPath, "")
                if not pathExists(pngname):  # no picon for service found
                    pngname = self.defaultpngname

                if self.pngname != pngname:
                    try:
                        if pngname != self.defaultpngname:
                            try:
                                im = Image.open(pngname).convert('RGBA').resize((self.piconsize), Image.Resampling.LANCZOS).save("/tmp/temppicons/" + str(tempname), "PNG")
                            except:
                                im = Image.open(pngname).convert('RGBA').resize((self.piconsize), Image.ANTIALIAS).save("/tmp/temppicons/" + str(tempname), "PNG")
                            self.instance.setScale(1)
                            self.instance.setPixmapFromFile("/tmp/temppicons/" + str(tempname))
                            self.instance.show()
                        elif pngname == self.defaultpngname:
                            try:
                                im = Image.open(pngname).convert('RGBA').resize((self.piconsize), Image.Resampling.LANCZOS).save("/tmp/temppicons/" + "picon_default.png", "PNG")
                            except:
                                im = Image.open(pngname).convert('RGBA').resize((self.piconsize), Image.ANTIALIAS).save("/tmp/temppicons/" + "picon_default.png", "PNG")
                            self.instance.setScale(1)
                            self.instance.setPixmapFromFile("/tmp/temppicons/picon_default.png")
                            self.instance.show()
                        else:
                            self.instance.hide()
                    except Exception as e:
                        print(e)
                        print("[Picon] Bad picon file?: %s" % pngname)
                        return

                    self.pngname = pngname
                    # delete any existing pngs
                    if os.path.exists('/tmp/temppicons'):
                        for filename in glob.glob('/tmp/temppicons/*.png'):
                            os.remove(filename)


harddiskmanager.on_partition_list_change.append(onPartitionChange)
initPiconPaths()
