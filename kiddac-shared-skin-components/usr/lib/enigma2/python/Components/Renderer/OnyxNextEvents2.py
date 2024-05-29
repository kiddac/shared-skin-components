from __future__ import absolute_import

from time import localtime
from enigma import eLabel, eEPGCache

from Components.Renderer.Renderer import Renderer
from Components.VariableText import VariableText

class OnyxNextEvents2(VariableText, Renderer):

    def __init__(self):
        self.lines = False
        Renderer.__init__(self)
        VariableText.__init__(self)
        self.epgcache = eEPGCache.getInstance()

    def applySkin(self, desktop, parent):
        self.number = 0
        self.start = 1
        self.start2 = 0
        attribs = []
        for (attrib, value) in self.skinAttributes:
            if attrib == "number":
                self.number = int(value)
            elif attrib == "lines":
                self.number = int(value) + 1
                self.lines = True
            elif attrib == "start":
                self.start = int(value)
                self.start2 = self.start - 1
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
            list = self.epgcache.lookupEvent(['BDT', (self.source.text, 0, -1, 1440)])
            text = ""
            if len(list):
                if self.lines:
                    i = 1
                    for event in list:
                        if len(event) == 3 and i == self.number + self.start2:
                            text = text + self.build_eventstr(event)
                            break
                        elif len(event) == 3 and i > self.start and ((self.number > 0 and i < (self.number + self.start2)) or self.number == 0):
                            text = text + self.build_eventstr(event)
                        i += 1
                        if i > 30:
                            break
                else:
                    i = 1
                    for event in list:
                        if len(event) == 3 and i == int(self.number):
                            text = text + self.build_eventstr(event)
                            break
                        elif len(event) == 3 and i > 1 and self.number == 0:
                            text = text + self.build_eventstr(event)
                        i += 1
                        if i > 30:
                            break
            self.text = text

    def build_eventstr(self, event):
        begin = localtime(event[0])
        trunc = 26
        suffix = ".."
        if len(event[2]) <= trunc:
            return("%02d:%02d  %s\n" % (begin[3], begin[4], event[2]))
        else:
            return("%02d:%02d  %s\n" % (begin[3], begin[4], event[2][:trunc] + suffix))
