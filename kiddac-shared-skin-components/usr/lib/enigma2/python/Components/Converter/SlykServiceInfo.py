from __future__ import absolute_import
from Components.Converter.Converter import Converter
from enigma import iServiceInformation, iPlayableService
from Components.Element import cached

WIDESCREEN = [1, 3, 4, 7, 8, 0xB, 0xC, 0xF, 0x10]


class SlykServiceInfo(Converter, object):
    IS_MULTICHANNEL = 1
    AUDIO_STEREO = 2
    IS_CRYPTED = 3
    IS_WIDESCREEN = 4
    XRES = 5
    YRES = 6
    HAS_HBBTV = 7
    SUBTITLES_AVAILABLE = 8
    IS_STREAM = 9
    IS_SD = 10
    IS_HD = 11
    IS_1080 = 12
    IS_720 = 13
    IS_576 = 14
    IS_480 = 15
    IS_4K = 16

    def __init__(self, type):
        Converter.__init__(self, type)
        self.type, self.interesting_events = {
            "IsMultichannel": (self.IS_MULTICHANNEL, (iPlayableService.evUpdatedInfo,)),
            "IsStereo": (self.AUDIO_STEREO, (iPlayableService.evUpdatedInfo,)),
            "IsCrypted": (self.IS_CRYPTED, (iPlayableService.evUpdatedInfo,)),
            "IsWidescreen": (self.IS_WIDESCREEN, (iPlayableService.evVideoSizeChanged,)),
            "HasHBBTV": (self.HAS_HBBTV, (iPlayableService.evUpdatedInfo, iPlayableService.evHBBTVInfo,)),
            "SubtitlesAvailable": (self.SUBTITLES_AVAILABLE, (iPlayableService.evUpdatedInfo,)),
            "IsStream": (self.IS_STREAM, (iPlayableService.evUpdatedInfo,)),
            "IsSD": (self.IS_SD, (iPlayableService.evVideoSizeChanged,)),
            "IsHD": (self.IS_HD, (iPlayableService.evVideoSizeChanged,)),
            "Is1080": (self.IS_1080, (iPlayableService.evVideoSizeChanged,)),
            "Is720": (self.IS_720, (iPlayableService.evVideoSizeChanged,)),
            "Is576": (self.IS_576, (iPlayableService.evVideoSizeChanged,)),
            "Is480": (self.IS_480, (iPlayableService.evVideoSizeChanged,)),
            "Is4K": (self.IS_4K, (iPlayableService.evVideoSizeChanged,)),
        }[type]

    def getServiceInfoString(self, info, what, convert=lambda x: "%d" % x):
        v = info.getInfo(what)
        if v == -1:
            return "N/A"
        if v == -2:
            return info.getInfoString(what)
        return convert(v)

    def _getProcVal(self, pathname, base=10):
        val = None
        try:
            f = open(pathname, "r")
            val = int(f.read(), base)
            f.close()
            if val >= 2 ** 31:
                val -= 2 ** 32
        except Exception as e:
            print(e)
            pass
        return val

    def _getVal(self, pathname, info, infoVal, base=10):
        val = self._getProcVal(pathname, base=base)
        return val if val is not None else info.getInfo(infoVal)

    def _getValInt(self, pathname, info, infoVal, base=10, default=-1):
        val = self._getVal(pathname, info, infoVal, base)
        return val if val is not None else default

    def _getValStr(self, pathname, info, infoVal, base=10, convert=lambda x: "%d" % x):
        val = self._getProcVal(pathname, base=base)
        return convert(val) if val is not None else self.getServiceInfoString(info, infoVal, convert)

    def _getVideoHeight(self, info):
        return self._getValInt("/proc/stb/vmpeg/0/yres", info, iServiceInformation.sVideoHeight, base=16)

    def _getVideoHeightStr(self, info, convert=lambda x: "%d" % x if x > 0 else "?"):
        return self._getValStr("/proc/stb/vmpeg/0/yres", info, iServiceInformation.sVideoHeight, base=16, convert=convert)

    def _getVideoWidth(self, info):
        return self._getValInt("/proc/stb/vmpeg/0/xres", info, iServiceInformation.sVideoWidth, base=16)

    def _getVideoWidthStr(self, info, convert=lambda x: "%d" % x if x > 0 else "?"):
        return self._getValStr("/proc/stb/vmpeg/0/xres", info, iServiceInformation.sVideoWidth, base=16, convert=convert)


    @cached
    def getBoolean(self):
        service = self.source.service
        info = service and service.info()
        if not info:
            return False
        video_height = None
        video_aspect = None
        video_height = self._getVideoHeight(info)
        video_aspect = info.getInfo(iServiceInformation.sAspect)

        if self.type in (self.IS_MULTICHANNEL, self.AUDIO_STEREO):
            audio = service.audioTracks()
            if audio:
                n = audio.getNumberOfTracks()
                idx = 0
                while idx < n:
                    i = audio.getTrackInfo(idx)
                    description = i.getDescription()
                    if description and description.split()[0] in ("AC3", "AC-3", "AC3+", "DTS"):  # some audio description has 'audio' as additional value (e.g. 'AC-3 audio')
                        if self.type == self.IS_MULTICHANNEL:
                            return True
                        elif self.type == self.AUDIO_STEREO:
                            return False
                    idx += 1
                if self.type == self.IS_MULTICHANNEL:
                    return False
                elif self.type == self.AUDIO_STEREO:
                    return True
            return False

        elif self.type == self.IS_CRYPTED:
            return info.getInfo(iServiceInformation.sIsCrypted) == 1

        elif self.type == self.IS_WIDESCREEN:
            return video_aspect in WIDESCREEN

        elif self.type == self.HAS_HBBTV:
            return info.getInfoString(iServiceInformation.sHBBTVUrl) != ""

        elif self.type == self.SUBTITLES_AVAILABLE:
            subtitle = service and service.subtitle()
            subtitlelist = subtitle and subtitle.getSubtitleList()
            if subtitlelist:
                return len(subtitlelist) > 0
            return False

        elif self.type == self.IS_STREAM:
            return service.streamed() is not None

        elif self.type == self.IS_SD:
            return video_height < 720

        elif self.type == self.IS_HD:
            return video_height >= 720 and video_height < 2160

        elif self.type == self.IS_1080:
            return video_height >= 1080 and video_height <= 2119

        elif self.type == self.IS_720:
            return video_height >= 720 and video_height <= 1079

        elif self.type == self.IS_576:
            return video_height >= 576 and video_height <= 719

        elif self.type == self.IS_480:
            return video_height > 0 and video_height <= 575

        elif self.type == self.IS_4K:
            return video_height >= 2160 and video_height < 4320

        else:
            return False

    boolean = property(getBoolean)

    @cached
    def getText(self):
        service = self.source.service
        info = service and service.info()
        if not info:
            return ""
        if self.type == self.XRES:
            return self._getVideoWidthStr(info)
        elif self.type == self.YRES:
            return self._getVideoHeightStr(info)

        elif self.type == self.HAS_HBBTV:
            return info.getInfoString(iServiceInformation.sHBBTVUrl)

        return ""

    text = property(getText)

    @cached
    def getValue(self):
        service = self.source.service
        info = service and service.info()
        if not info:
            return -1

        if self.type == self.XRES:
            return str(self._getVideoWidth(info))
        elif self.type == self.YRES:
            return str(self._getVideoHeight(info))

        return -1

    value = property(getValue)

    def changed(self, what):
        if what[0] != self.CHANGED_SPECIFIC or what[1] in self.interesting_events:
            Converter.changed(self, what)
