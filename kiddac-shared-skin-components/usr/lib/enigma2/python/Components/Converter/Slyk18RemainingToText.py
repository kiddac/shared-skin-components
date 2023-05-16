from __future__ import absolute_import
from Components.Converter.Converter import Converter
# from time import time as getTime, localtime, strftime
from Components.Converter.Poll import Poll
from Components.Element import cached
from Components.config import config
from gettext import ngettext

# OnlyMinute = Started %d min ago / Started %d mins ago


class Slyk18RemainingToText(Poll, Converter, object):
    ONLY_MINUTE = 5

    def __init__(self, type):
        Poll.__init__(self)
        Converter.__init__(self, type)
        if type == "OnlyMinute":
            self.type = self.ONLY_MINUTE

        if config.usage.swap_time_display_on_osd.value == "1" or config.usage.swap_time_display_on_osd.value == "3" or config.usage.swap_time_display_on_osd.value == "5":
            self.poll_interval = 1000
            self.poll_enabled = True
        if config.usage.swap_time_display_on_osd.value == "2" or config.usage.swap_time_display_on_osd.value == "4":
            self.poll_interval = 1000
            self.poll_enabled = True

    @cached
    def getText(self):
        time = self.source.time
        if time is None:
            return ""

        duration = 0
        elapsed = 0
        remaining = 0

        if str(time[1]) != 'None':
            if self.type < 7:
                if config.usage.swap_time_remaining_on_osd.value == "0":
                    (duration, remaining) = self.source.time
                    r = remaining
                elif config.usage.swap_time_remaining_on_osd.value == "1":
                    (duration, elapsed) = self.source.time
                    r = duration - elapsed
                elif config.usage.swap_time_remaining_on_osd.value == "2":
                    (duration, elapsed, remaining) = self.source.time
                    r = elapsed
                elif config.usage.swap_time_remaining_on_osd.value == "3":
                    (duration, remaining, elapsed) = self.source.time
                    r = elapsed
            else:
                if config.usage.swap_time_remaining_on_vfd.value == "0":
                    (duration, remaining) = self.source.time
                elif config.usage.swap_time_remaining_on_vfd.value == "1":
                    (duration, elapsed) = self.source.time
                elif config.usage.swap_time_remaining_on_vfd.value == "2":
                    (duration, elapsed, remaining) = self.source.time
                elif config.usage.swap_time_remaining_on_vfd.value == "3":
                    (duration, remaining, elapsed) = self.source.time
        else:
            (duration, remaining) = self.source.time
            r = remaining

        length = duration   # Length
        # p = elapsed   # Position

        if self.type == self.ONLY_MINUTE:
            if remaining is not None:
                return ngettext(_("Started %d min ago"), _("Started %d mins ago"), (r // 60)) % (r // 60)
        else:
            return "%d" % length

    text = property(getText)
