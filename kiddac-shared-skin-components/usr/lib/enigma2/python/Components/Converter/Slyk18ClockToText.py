from __future__ import absolute_import
from Components.Converter.Converter import Converter
from time import localtime, strftime, time as getTime
from Components.Element import cached
from Components.config import config

import os.path
from gettext import ngettext

# Slyk18ClockToText

# Slyk18AsLength = 1 min / 2 mins / 1 Hour / 2 Hours
# Slyk18DateFormat1 = Full Day - (0-12)hour - (00-59)min - am/pm : Monday 4.19am
# Slyk18DateFormat2 = (0-12)hour - (00-59)min - am/pm - Abbr Week - Decimal Day(0-31) - Decimal Month(01-12) : 4.28pm Sun 20/11
# Slyk18Time = (0-12)hour - (00-59)min - am/pm : 4.28pm
# Slyk18StartedAt = Started at/Starts at - (0-12)hour - (00-59)min - am/pm : Started at 4.28pm

# config.osd = ConfigSubsection()
hours24 = True
filename = '/usr/share/enigma2/slyk-common/timeformat.txt'

if config.osd.language.value == "en_GB" or config.osd.language.value == "en_US" or config.osd.language.value == "en_AU":
    hours24 = False

if os.path.exists(filename):
    with open(filename, "r") as myfile:
        if 'Time = 24' in myfile.read():
            hours24 = True


class Slyk18ClockToText(Converter, object):
    DEFAULT = 0
    FORMAT = 1
    SLYK18_AS_LENGTH = 2
    SLYK18_DATE_FORMAT1 = 3
    SLYK18_DATE_FORMAT2 = 4
    SLYK18_TIME = 5
    SLYK18_STARTEDATE = 6
    FULL = 7

    def __init__(self, type):
        Converter.__init__(self, type)

        self.fix = ""
        if ';' in type:
            type, self.fix = type.split(';')

        if type == "Slyk18AsLength":
            self.type = self.SLYK18_AS_LENGTH
        elif type == "Slyk18DateFormat1":
            self.type = self.SLYK18_DATE_FORMAT1
        elif type == "Slyk18DateFormat2":
            self.type = self.SLYK18_DATE_FORMAT2
        elif type == "Slyk18Time":
            self.type = self.SLYK18_TIME
        elif type == "Slyk18StartedAt":
            self.type = self.SLYK18_STARTEDATE
        elif type == "Full":
            self.type = self.FULL
        elif "Format" in type:
            self.type = self.FORMAT
            self.fmt_string = type[7:]
        else:
            self.type = self.DEFAULT

    @cached
    def getText(self):
        time = self.source.time
        t = localtime(time)
        tnow = getTime()

        if time is None:
            return ""

        def fix_space(string):
            if "Proportional" in self.fix and t.tm_hour < 10:
                return " " + string
            if "NoSpace" in self.fix:
                return string.lstrip()
            return string

        if self.type == self.SLYK18_AS_LENGTH:
            # below is 9 to not show duration on directories for movies
            if time <= 9:
                return ""
            else:
                if time / 3600 < 1:
                    return ngettext(_("%d Min"), _("%d Mins"), (time // 60)) % (time // 60)
                elif time / 60 % 60 == 0:
                    return ngettext(_("%d Hour"), _("%d Hours"), (time // 3600)) % (time // 3600)
                else:
                    return "%dh %2dm" % (time // 3600, time // 60 % 60)

        if int(strftime("%H", t)) >= 12:
            timesuffix = _('pm')
        else:
            timesuffix = _('am')

        if self.type == self.DEFAULT:
            return fix_space(_("%2d:%02d") % (t.tm_hour, t.tm_min))

        elif self.type == self.SLYK18_DATE_FORMAT1:
            if hours24:
                d = _("%A, %H.%M")
            else:
                d = _("%A, %l.%M") + _(timesuffix)

        elif self.type == self.SLYK18_DATE_FORMAT2:
            if hours24:
                d = _("%H.%M") + _(" %a %d/%m")
            else:
                d = _("%l.%M") + _(timesuffix) + _(" %a %d/%m")

        elif self.type == self.SLYK18_TIME:
            if hours24:
                d = _("%H.%M")
            else:
                d = _("%l.%M") + _(timesuffix)

        elif self.type == self.SLYK18_STARTEDATE:
            if hours24:
                if time < tnow:
                    d = _('Started at') + ' ' + _("%H.%M").lstrip()
                else:
                    d = _('Starts at') + ' ' + _("%H.%M").lstrip()
            else:
                if time < tnow:
                    d = _('Started at') + ' ' + _("%l.%M").lstrip() + _(timesuffix)
                else:
                    d = _('Starts at') + ' ' + _("%l.%M").lstrip() + _(timesuffix)

        elif self.type == self.FULL:
            d = _("%a %e/%m  %-H:%M")

        elif self.type == self.FORMAT:
            d = self.fmt_string

        else:
            return "???"

        timetext = strftime(d, t)

        return timetext.lstrip(' ')

    text = property(getText)
