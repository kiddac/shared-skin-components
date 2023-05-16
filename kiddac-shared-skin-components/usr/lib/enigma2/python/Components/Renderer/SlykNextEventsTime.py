from __future__ import absolute_import
from Components.VariableText import VariableText
from Components.Renderer.Renderer import Renderer
from enigma import eLabel, eEPGCache
from time import localtime, strftime
import os.path


hours24 = False
filename = '/usr/share/enigma2/slyk-common/timeformat.txt'


if os.path.exists(filename):
    with open(filename, "r") as myfile:
        if 'Time = 24' in myfile.read():
            hours24 = True
        else:
            hours24 = False


class SlykNextEventsTime(VariableText, Renderer):
    def __init__(self):
        Renderer.__init__(self)
        VariableText.__init__(self)
        self.epgcache = eEPGCache.getInstance()

    def applySkin(self, desktop, parent):
        self.number = 3
        attribs = []
        for (attrib, value) in self.skinAttributes:
            if attrib == "number":
                self.number = int(value)
            else:
                attribs.append((attrib, value))
        self.skinAttributes = attribs
        return Renderer.applySkin(self, desktop, parent)

    GUI_WIDGET = eLabel

    def connect(self, source):
        Renderer.connect(self, source)
        self.changed((self.CHANGED_DEFAULT,))

    def changed(self, what):
        if what[0] == self.CHANGED_CLEAR:
            self.text = ""
        else:
            list = self.epgcache.lookupEvent(['BDT', (self.source.text, 0, -1, 360)])
            text = ""
            if len(list):
                i = 1
                for event in list:
                    if len(event) == 3 and i == int(self.number):
                        t = localtime(event[0])

                        if int(strftime("%H", t)) >= 12:
                            timesuffix = _('pm')
                        else:
                            timesuffix = _('am')
                        if hours24:
                            text = strftime("%H", t) + "." + strftime("%M", t)
                        else:
                            text = strftime("%l", t) + "." + strftime("%M", t) + timesuffix

                        break
                    i = i + 1
                    if i >= len(list):
                        break
            self.text = text
