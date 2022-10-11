import re
from enum import Enum
from pathlib import Path

from trafficgenerator import TgnError

from ixexplorer.api.ixapi import FLAG_IGERR, FLAG_RDONLY, MacStr, TclMember, ixe_obj_meta
from ixexplorer.ixe_object import IxeObject, IxeObjectObj
from ixexplorer.ixe_statistics_view import IxeCapFileFormat, IxePortsStats, IxeStat, IxeStreamsStats
from ixexplorer.ixe_stream import IxeStream


class IxePhyMode(Enum):
    copper = "portPhyModeCopper"
    fiber = "portPhyModeFibber"
    sgmii = "portPhyModeSgmii"
    ignore = None


class IxeReceiveMode(Enum):
    none = 0x0000
    capture = 0x0001
    packetGroup = 0x0002
    tcpSessions = 0x0004
    tcpRoundTrip = 0x0008
    dataIntegrity = 0x0010
    firstTimeStamp = 0x0020
    sequenceChecking = 0x0040
    bert = 0x0080
    isl = 0x0100
    bertChannelized = 0x0200
    echo = 0x0400
    dcc = 0x0800
    widePacketGroup = 0x1000
    prbs = 0x2000
    rateMonitoring = 0x4000
    perFlowErrorStats = 0x8000


class IxeTransmitMode(Enum):
    packetStreams = "portTxPacketStreams"
    packetFlows = "portTxPacketFlows"
    advancedScheduler = "portTxModeAdvancedScheduler"
    bert = "portTxModeBert"
    bertChannelized = "portTxModeBertChannelized"
    echo = "portTxModeEcho"
    dccStreams = "portTxModeDccStreams"
    dccAdvancedScheduler = "portTxModeDccAvancedScheduler"
    dccFlowSpecStreams = "portTxModeDccFlowsSpeStreams"
    dccFlowSpecAdvancedScheduler = "portTxModeDccFlowsSpeAdvancedScheduler"
    advancedSchedulerCoarse = "portTxModeAdvancedSchedulerCoarse"
    streamsCoarse = "portTxModePacketStreamsCoarse"


class IxeLinkState(Enum):
    linkDown = 0
    linkUp = 1
    linkLoopback = 2
    noTransceiver = 7
    invalidAddress = 8
    noGbicModule = 13
    lossOfFrame = 24
    lossOfSignal = 25
    forcedLinkUp = 34
    noXenpakModule = 40
    demoMode = 42
    noXFPModule = 45
    inactive = 47
    noX2Module = 48
    ethernetOamLoopback = 54


class StreamWarningsError(TgnError):
    pass


class IxePort(IxeObject, metaclass=ixe_obj_meta):
    __tcl_command__ = "port"
    __tcl_members__ = [
        TclMember("advertise2P5FullDuplex", type=int, flags=FLAG_IGERR),
        TclMember("advertise5FullDuplex", type=int, flags=FLAG_IGERR),
        TclMember("advertise1000FullDuplex", type=bool),
        TclMember("advertise100FullDuplex", type=bool),
        TclMember("advertise100HalfDuplex", type=bool),
        TclMember("advertise10FullDuplex", type=bool),
        TclMember("advertise10HalfDuplex", type=bool),
        TclMember("advertiseAbilities"),
        TclMember("autoDetectInstrumentationMode", type=bool),
        TclMember("autonegotiate", type=bool),
        TclMember("dataCenterMode"),
        TclMember("DestMacAddress", type=MacStr),
        TclMember("directedAddress"),
        TclMember("duplex"),
        TclMember("enableAutoDetectInstrumentation", type=bool),
        TclMember("enableDataCenterMode", type=bool),
        TclMember("enableManualAutoNegotiate", type=bool),
        TclMember("enablePhyPolling", type=bool),
        TclMember("enableRepeatableLastRandomPattern", type=bool),
        TclMember("enableSimulateCableDisconnect", type=bool),
        TclMember("enableTransparentDynamicRateChange", type=bool),
        TclMember("enableTxRxSyncStatsMode", type=bool),
        TclMember("flowControl", type=bool),
        TclMember("flowControlType", int),
        TclMember("ignoreLink", type=bool),
        TclMember("linkState", type=int, flags=FLAG_RDONLY),
        TclMember("loopback"),
        TclMember("MacAddress", type=MacStr),
        TclMember("masterSlave"),
        TclMember("multicastPauseAddress"),
        TclMember("negotiateMasterSlave", type=bool),
        TclMember("operationModeList"),
        TclMember("owner"),
        TclMember("packetFlowFileName"),
        TclMember("pfcEnableValueList"),
        TclMember("pfcEnableValueListBitMatrix"),
        TclMember("pfcResponseDelayEnabled"),
        TclMember("pfcResponseDelayQuanta"),
        TclMember("phyMode", flags=FLAG_RDONLY),
        TclMember("pmaClock", type=int),
        TclMember("portMode", type=int),
        TclMember("preEmphasis"),
        TclMember("receiveMode", type=int),
        TclMember("rxTxMode", type=int),
        TclMember("speed", type=int),
        TclMember("timeoutEnable"),
        TclMember("transmitClockDeviation", type=bool),
        TclMember("transmitClockMode", type=int),
        TclMember("transmitMode"),
        TclMember("txRxSyncInterval", type=int),
        TclMember("type", flags=FLAG_RDONLY),
        TclMember("typeName", flags=FLAG_RDONLY),
        TclMember("usePacketFlowImageFile", type=bool),
        TclMember("enableRsFec", type=bool),
        TclMember("ieeeL1Defaults", type=int),
    ]

    __tcl_commands__ = [
        "export",
        "getFeature",
        "getStreamCount",
        "reset",
        "setFactoryDefaults",
        "setModeDefaults",
        "restartAutoNegotiation",
        "getPortState",
        "isValidFeature",
        "isActiveFeature",
        "isCapableFeature",
    ]

    mode_2_speed = {
        "0": "10000",
        "5": "100000",
        "6": "40000",
        "7": "100000",
        "8": "40000",
        "9": "10000",
        "10": "10000",
        "18": "25000",
        "19": "50000",
        "20": "25000",
    }

    def __init__(self, parent, uri):
        super().__init__(parent=parent, uri=uri.replace("/", " "))
        self.cap_file_name = None

    def supported_speeds(self):
        # todo FIX  once parent is Session(by reserve_ports) - no active_ports ,only if parent is card(by discover)!!!
        # if self.parent.active_ports == self.parent.ports:
        supported_speeds = re.findall(r"\d+", self.getFeature("ethernetLineRate"))
        # Either active_ports != self.parent.ports or empty supported speeds for whatever reason...
        if not supported_speeds:
            for rg in self.parent.resource_groups.values():
                if self.index in rg.active_ports:
                    speed = rg.mode if int(rg.mode) >= 1000 else self.mode_2_speed.get(rg.mode, rg.mode)
                    supported_speeds = [speed]
                    break
        return supported_speeds

    def reserve(self, force: bool = False) -> None:
        """Reserve port.

        :param force: True - take forcefully, False - fail if port is reserved by other user.
        """
        if force:
            self.api.call_rc(f"ixPortTakeOwnership {self.uri} force")
        else:
            try:
                self.api.call_rc(f"ixPortTakeOwnership {self.uri}")
            except Exception:
                raise TgnError(f"Failed to take ownership for port {self} current owner is {self.owner}")

    def release(self, force: bool = False) -> None:
        """Release port.

        :param force: True - release forcefully, False - fail if port is reserved by other user.
        """
        if force:
            self.api.call_rc(f"ixPortClearOwnership {self.uri} force")
        else:
            try:
                self.api.call_rc(f"ixPortClearOwnership {self.uri}")
            except Exception:
                raise TgnError(f"Failed to clear ownership for port {self} current owner is {self.owner}")

    def write(self) -> None:
        """Write configuration to chassis.

        Raise StreamWarningsError if configuration warnings found.
        """
        self.ix_command("write")
        stream_warnings = self.streamRegion.generateWarningList()
        warnings_list = (
            self.api.call("join " + " {" + stream_warnings + "} " + " LiStSeP").split("LiStSeP")
            if self.streamRegion.generateWarningList()
            else []
        )
        for warning in warnings_list:
            if warning:
                raise StreamWarningsError(warning)

    def clear(self, stats: bool = True, phy_mode: IxePhyMode = IxePhyMode.ignore) -> None:
        self.ix_set_default()
        self.setFactoryDefaults()
        self.set_phy_mode(phy_mode)
        self.reset()
        self.write()
        if stats:
            self.clear_port_stats()
            self.clear_all_stats()
            self.del_objects_by_type("stream")

    def load_config(self, config_file: Path) -> None:
        """Load configuration file from prt or str.

        Configuration file type is extracted from the file suffix - prt or str.

        :TODO: Investigate why port import can only import files that were exported with port export, not from File -> export.

        :param config_file: full path to the configuration file.
            IxTclServer must have access to the file location. either:
                The config file is on shared folder.
                IxTclServer run on the client machine.
        """
        ext = config_file.suffix
        if ext == ".prt":
            self.api.call_rc(f'port import "{config_file}" {self.uri}')
        elif ext == ".str":
            self.reset()
            self.api.call_rc(f'stream import "{config_file}" {self.uri}')
        else:
            raise ValueError(f"Configuration file type {ext} not supported.")
        self.write()
        self.discover()

    def save_config(self, config_file: Path) -> None:
        """Save configuration file from prt or str.

        Configuration file type is extracted from the file suffix - prt or str.

        :param config_file: full path to the configuration file.
            IxTclServer must have access to the file location. either:
                The config file is on shared folder.
                IxTclServer run on the client machine.
        """
        ext = config_file.suffix
        if ext == ".prt":
            self.api.call_rc(f'port export "{config_file}" {self.uri}')
        elif ext == ".str":
            self.api.call_rc(f'stream export "{config_file}" {self.uri}')
        else:
            raise ValueError(f"Configuration file type {ext} not supported.")

    def wait_for_up(self, timeout: int = 16) -> None:
        """Wait until port is up and running.

        :param timeout: seconds to wait.
        """
        self.session.wait_for_up(timeout, [self])

    def discover(self) -> None:
        self.logger.info("Discover port {}".format(self.obj_name()))
        for stream_id in range(1, int(self.getStreamCount()) + 1):
            IxeStream(self, self.uri + "/" + str(stream_id))

    def start_transmit(self, blocking: bool = False) -> None:
        """Start transmit on port.

        :param blocking: True - wait for traffic end, False - return after traffic start.
        """
        self.session.start_transmit(blocking, False, self)

    def stop_transmit(self) -> None:
        """Stop traffic on port."""
        self.session.stop_transmit(self)

    def start_capture(self) -> None:
        """Start capture on port."""
        self.session.start_capture(self)

    def stop_capture(self, cap_file_name: str = None, cap_file_format: IxeCapFileFormat = IxeCapFileFormat.mem) -> int:
        """Stop capture on port.

        :param cap_file_name: prefix for the capture file name.
            Capture file will be saved as pcap file named 'prefix' + 'URI'.pcap.
        :param cap_file_format: exported file format
        :return: number of captured frames
        """
        return self.session.stop_capture(cap_file_name, cap_file_format, self)[self]

    def get_cap_file(self):
        return self.session.get_cap_files(self)[self]

    def get_cap_frames(self, *frame_nums):
        """Stop capture on ports.

        :param frame_nums: list of frame numbers to read.
        :return: list of captured frames.
        """
        frames = []
        for frame_num in frame_nums:
            if self.captureBuffer.getframe(frame_num) == "0":
                frames.append(self.captureBuffer.frame)
            else:
                frames.append(None)
        return frames

    #
    # Statistics.
    #

    def clear_port_stats(self) -> None:
        """Clear only port stats (leave stream and packet group stats).

        Do not use - still working with Ixia to resolve.
        """
        stat = IxeStat(self)
        stat.ix_set_default()
        stat.enableValidStats = True
        stat.ix_set()
        stat.write()

    def clear_all_stats(self) -> None:
        """Clear all statistic counters (port, streams and packet groups) on list of ports."""
        self.session.clear_all_stats(self)

    def read_stats(self, *stats):
        return IxePortsStats(self).read_stats(*stats)[str(self)]

    def read_stream_stats(self, *stats):
        return IxeStreamsStats(*self.get_objects_by_type("stream")).read_stats(*stats)

    #
    # Others...
    #

    def set_phy_mode(self, mode=IxePhyMode.ignore):
        """Set phy mode to copper or fiber.
        :param mode: requested PHY mode.
        """
        if isinstance(mode, IxePhyMode):
            if mode.value:
                self.api.call_rc("port setPhyMode {} {}".format(mode.value, self.uri))
        else:
            self.api.call_rc(
                "port setPhyMode {} {}".format(
                    mode,
                    self.uri,
                )
            )

    def set_receive_modes(self, *modes):
        """Set port receive modes (overwrite existing value).

        :param modes: requested receive modes
        :type modes: list[ixexplorer.ixe_port.IxeReceiveMode]
        """

        self._set_receive_modes(0, *modes)

    def add_receive_modes(self, *modes):
        """Add port receive modes to exiting modes.

        :param modes: requested receive modes
        :type modes: list[ixexplorer.ixe_port.IxeReceiveMode]
        """

        self._set_receive_modes(self.receiveMode, *modes)

    def set_transmit_mode(self, mode):
        """set port transmit mode

        :param mode: request transmit mode
        :type mode: ixexplorer.ixe_port.IxeTransmitMode
        """

        self.api.call_rc("port setTransmitMode {} {}".format(mode, self.uri))

    def set_rx_ports(self, *rx_ports):
        for stream in self.get_objects_by_type("stream"):
            stream.rx_ports = rx_ports

    rx_ports = property(fset=set_rx_ports)

    def ix_set_list(self, optList):
        self.ix_get()
        for opt in optList:
            value = optList[opt]
            self.api.call("%s config -%s %s" % (self.__tcl_command__, opt, value))
        self.ix_set()

    def set_wide_packet_group(self) -> None:
        self.set_receive_modes(IxeReceiveMode.widePacketGroup, IxeReceiveMode.dataIntegrity)

    def add_stream(self, name: str = None) -> IxeStream:
        stream = IxeStream(self, f"{self.uri} {str(int(self.getStreamCount()) + 1)}")
        stream.create(name)
        return stream

    #
    # Port objects.
    #

    def get_autoDetectInstrumentation(self):
        return self._get_object("_autoDetectInstrumentation", IxeAutoDetectInstrumentationPort)

    autoDetectInstrumentation = property(get_autoDetectInstrumentation)

    def get_capture(self):
        return self._get_object("_capture", IxeCapture)

    capture = property(get_capture)

    def get_captureBuffer(self):
        return self._get_object("_captureBuffer", IxeCaptureBuffer)

    def set_captureBuffer(self, value):
        self._captureBuffer = value

    captureBuffer = property(fget=get_captureBuffer, fset=set_captureBuffer)

    def get_dataIntegrity(self):
        return self._get_object("_dataIntegrity", IxeDataIntegrityPort)

    dataIntegrity = property(get_dataIntegrity)

    def get_filter(self):
        return self._get_object("_filter", IxeFilterPort)

    filter = property(get_filter)

    def get_filterPallette(self):
        return self._get_object("_filterPallette", IxeFilterPalettePort)

    filterPallette = property(get_filterPallette)

    def get_packetGroup(self):
        return self._get_object("_packetGroup", IxePacketGroupPort)

    packetGroup = property(get_packetGroup)

    def get_splitPacketGroup(self):
        return self._get_object("_splitPacketGroup", IxeSplitPacketGroup)

    splitPacketGroup = property(get_splitPacketGroup)

    def get_streamRegion(self):
        return self._get_object("_streamRegion", IxeStreamRegion)

    streamRegion = property(get_streamRegion)

    #
    # Properties.
    #

    def get_streams(self):
        """
        :return: dictionary {stream id: object} of all streams.
        """

        return {int(s.index): s for s in self.get_objects_by_type("stream")}

    streams = property(get_streams)

    #
    # Private methods.
    #

    def _set_receive_modes(self, receiveMode, *modes):
        for mode in modes:
            receiveMode += mode.value
        self.receiveMode = receiveMode


#
# Port object classes.
#


class IxePortObj(IxeObjectObj):
    def __init__(self, parent):
        super().__init__(parent=parent, uri=parent.uri)


class IxeCapture(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "capture"
    __tcl_members__ = [
        TclMember("afterTriggerFilter"),
        TclMember("beforeTriggerFilter"),
        TclMember("captureMode"),
        TclMember("continuousFilter"),
        TclMember("enableSmallPacketCapture"),
        TclMember("fullAction"),
        TclMember("nPackets", type=int, flags=FLAG_RDONLY),
        TclMember("sliceSize"),
        TclMember("triggerPosition"),
    ]


class IxeCaptureBuffer(IxeObject, metaclass=ixe_obj_meta):
    __tcl_command__ = "captureBuffer"
    __tcl_members__ = [
        TclMember("frame", flags=FLAG_RDONLY),
    ]
    __tcl_commands__ = ["export", "getframe"]

    def __init__(self, parent):
        super().__init__(parent=parent, uri=parent.uri)
        if not self.parent.capture.nPackets:
            return
        self.api.call_rc("captureBuffer get {} 1 {}".format(self.uri, self.parent.capture.nPackets))

    def ix_command(self, command, *args, **kwargs):
        return self.api.call(("captureBuffer {} " + len(args) * " {}").format(command, *args))

    def ix_get(self, member=None, force=False):
        pass


class IxeFilterPalettePort(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "filterPallette"
    __tcl_members__ = [
        TclMember("DA1"),
        TclMember("DAMask1"),
        TclMember("DA2"),
        TclMember("DAMask2"),
        TclMember("SA1"),
        TclMember("SAMask1"),
        TclMember("SA2"),
        TclMember("SAMask2"),
        TclMember("pattern1"),
        TclMember("patternMask1"),
        TclMember("pattern2"),
        TclMember("patternMask2"),
        TclMember("patternOffset1", type=int),
        TclMember("patternOffset2", type=int),
    ]


class IxeFilterPort(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "filter"
    __tcl_members__ = [
        TclMember(""),
        TclMember("captureTriggerDA"),
        TclMember("captureTriggerSA"),
        TclMember("captureTriggerPattern"),
        TclMember("captureTriggerError"),
        TclMember("captureTriggerFrameSizeEnable"),
        TclMember("captureTriggerFrameSizeFrom"),
        TclMember("captureTriggerFrameSizeTo"),
        TclMember("captureTriggerCircuit"),
        TclMember("captureFilterDA"),
        TclMember("captureFilterSA"),
        TclMember("captureFilterPattern"),
        TclMember("captureFilterError"),
        TclMember("captureFilterFrameSizeEnable"),
        TclMember("captureFilterFrameSizeFrom"),
        TclMember("captureFilterFrameSizeTo"),
        TclMember("captureFilterCircuit"),
        TclMember("userDefinedStat1DA"),
        TclMember("userDefinedStat1SA"),
        TclMember("userDefinedStat1Pattern"),
        TclMember("userDefinedStat1Error"),
        TclMember("userDefinedStat1FrameSizeEnable"),
        TclMember("userDefinedStat1FrameSizeFrom"),
        TclMember("userDefinedStat1FrameSizeTo"),
        TclMember("userDefinedStat1Circuit"),
        TclMember("userDefinedStat2DA"),
        TclMember("userDefinedStat2SA"),
        TclMember("userDefinedStat2Pattern"),
        TclMember("userDefinedStat2Error"),
        TclMember("userDefinedStat2FrameSizeEnable"),
        TclMember("userDefinedStat2FrameSizeFrom"),
        TclMember("userDefinedStat2FrameSizeTo"),
        TclMember("userDefinedStat2Circuit"),
        TclMember("asyncTrigger1DA"),
        TclMember("asyncTrigger1SA"),
        TclMember("asyncTrigger1Pattern"),
        TclMember("asyncTrigger1Error"),
        TclMember("asyncTrigger1FrameSizeEnable"),
        TclMember("asyncTrigger1FrameSizeFrom"),
        TclMember("asyncTrigger1FrameSizeTo"),
        TclMember("asyncTrigger1Circuit"),
        TclMember("asyncTrigger2DA"),
        TclMember("asyncTrigger2SA"),
        TclMember("asyncTrigger2Pattern"),
        TclMember("asyncTrigger2Error"),
        TclMember("asyncTrigger2FrameSizeEnable"),
        TclMember("asyncTrigger2FrameSizeFrom"),
        TclMember("asyncTrigger2FrameSizeTo"),
        TclMember("asyncTrigger2Circuit"),
        TclMember("captureTriggerEnable"),
        TclMember("captureFilterEnable"),
        TclMember("userDefinedStat1Enable"),
        TclMember("userDefinedStat2Enable"),
        TclMember("asyncTrigger1Enable"),
        TclMember("asyncTrigger2Enable"),
        TclMember("userDefinedStat1PatternExpressionEnable"),
        TclMember("userDefinedStat2PatternExpressionEnable"),
        TclMember("captureTriggerPatternExpressionEnable"),
        TclMember("captureFilterPatternExpressionEnable"),
        TclMember("asyncTrigger1PatternExpressionEnable"),
        TclMember("asyncTrigger2PatternExpressionEnable"),
        TclMember("userDefinedStat1PatternExpression"),
        TclMember("userDefinedStat2PatternExpression"),
        TclMember("captureTriggerPatternExpression"),
        TclMember("captureFilterPatternExpression"),
        TclMember("asyncTrigger1PatternExpression"),
        TclMember("asyncTrigger2PatternExpression"),
    ]


class IxeSplitPacketGroup(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "splitPacketGroup"
    __tcl_members__ = [
        TclMember("groupIdOffset", type=int),
        TclMember("groupIdOffsetBaseType"),
        TclMember("groupIdWidth", type=int),
        TclMember("groupIdMask"),
    ]

    def __init__(self, parent):
        super().__init__(parent)
        self.ix_set_default()


class IxeStreamRegion(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "streamRegion"
    __tcl_commands__ = ["generateWarningList"]


#
# RX port object classes.
#


class IxePortRxObj(IxePortObj, metaclass=ixe_obj_meta):
    __get_command__ = "getRx"
    __set_command__ = "setRx"


class IxeAutoDetectInstrumentationPort(IxePortRxObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "autoDetectInstrumentation"
    __tcl_members__ = [
        TclMember("enableMisdirectedPacketMask", type=bool),
        TclMember("enablePRBS", type=bool),
        TclMember("enableSignatureMask", type=bool),
        TclMember("misdirectedPacketMask"),
        TclMember("signature"),
        TclMember("signatureMask"),
        TclMember("startOfScan", type=int),
    ]


class IxeDataIntegrityPort(IxePortRxObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "dataIntegrity"
    __tcl_members__ = [
        TclMember("enableTimeStamp", type=bool),
        TclMember("insertSignature", type=bool),
        TclMember("floatingTimestampAndDataIntegrityMode"),
        TclMember("numBytesFromEndOfFrame", type=int),
        TclMember("payloadLength", type=int),
        TclMember("signature"),
        TclMember("signatureOffset", type=int),
    ]


class IxePacketGroupPort(IxePortRxObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "packetGroup"
    __tcl_members__ = [
        TclMember("allocateUdf", type=bool),
        TclMember("delayVariationMode"),
        TclMember("enable128kBinMode", type=bool),
        TclMember("enableGroupIdMask", type=bool),
        TclMember("enableInsertPgid", type=bool),
        TclMember("enableLastBitTimeStamp", type=bool),
        TclMember("enableLatencyBins", type=bool),
        TclMember("enableReArmFirstTimeStamp", type=bool),
        TclMember("enableRxFilter", type=bool),
        TclMember("enableSignatureMask", type=bool),
        TclMember("enableTimeBins", type=bool),
        TclMember("groupId", type=int),
        TclMember("groupIdMask"),
        TclMember("groupIdMode"),
        TclMember("groupIdOffset", type=int),
        TclMember("headerFilter"),
        TclMember("headerFilterMask"),
        TclMember("ignoreSignature", type=bool),
        TclMember("insertSequenceSignature", type=bool),
        TclMember("insertSignature", type=bool),
        TclMember("latencyBinList"),
        TclMember("latencyControl"),
        TclMember("maxRxGroupId", type=int),
        TclMember("measurementMode"),
        TclMember("multiSwitchedPathMode"),
        TclMember("numPgidPerTimeBin", type=int),
        TclMember("numTimeBins", type=int),
        TclMember("preambleSize", type=int),
        TclMember("seqAdvTrackingLateThreshold", type=int),
        TclMember("sequenceErrorThreshold", type=int),
        TclMember("sequenceCheckingMode"),
        TclMember("sequenceNumberOffset", type=int),
        TclMember("signature"),
        TclMember("signatureMask"),
        TclMember("signatureOffset", type=int),
        TclMember("timeBinDuration", type=int),
    ]


class IxePortCpu(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "portCpu"
    __tcl_members__ = []

    __tcl_commands__ = [
        "reset",
    ]

    def reset_cpu(self) -> None:
        if self.parent.isValidFeature("portFeatureLocalCPU"):
            self.reset()
