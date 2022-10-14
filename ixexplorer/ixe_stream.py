from ixexplorer.api.ixapi import FLAG_RDONLY, MacStr, TclMember, ixe_obj_meta
from ixexplorer.ixe_object import IxeObject, IxeObjectObj
from ixexplorer.ixe_statistics_view import IxeStreamsStats


class IxeStream(IxeObject, metaclass=ixe_obj_meta):
    __tcl_command__ = "stream"
    __tcl_members__ = [
        TclMember("asyncIntEnable"),
        TclMember("bpsRate", type=float),
        TclMember("da", type=MacStr),
        TclMember("daMaskSelect"),
        TclMember("daMaskValue", type=MacStr),
        TclMember("daRepeatCounter"),
        TclMember("daStep", type=int),
        TclMember("dataPattern"),
        TclMember("dma"),
        TclMember("enable", type=bool),
        TclMember("enableDaContinueFromLastValue"),
        TclMember("enableIbg", type=bool),
        TclMember("enableIncrFrameBurstOverride", type=bool),
        TclMember("enableIsg", type=bool),
        TclMember("enableSaContinueFromLastValue"),
        TclMember("enableSourceInterface"),
        TclMember("enableStatistic"),
        TclMember("enableSuspend", type=bool),
        TclMember("enableTimestamp", type=bool),
        TclMember("enforceMinGap", type=bool),
        TclMember("fcs"),
        TclMember("fpsRate", type=float),
        TclMember("framesize", type=int),
        TclMember("frameSizeMAX", type=int),
        TclMember("frameSizeMIN", type=int),
        TclMember("frameSizeStep", type=int),
        TclMember("frameSizeType", type=int),
        TclMember("frameType"),
        TclMember("gapUnit"),
        TclMember("ibg", type=float),
        TclMember("ifg", type=float),
        TclMember("ifgMAX", type=float),
        TclMember("ifgMIN", type=float),
        TclMember("ifgType"),
        TclMember("isg", type=float),
        TclMember("loopCount", type=int),
        TclMember("name"),
        TclMember("numBursts", type=int),
        TclMember("numDA", type=int),
        TclMember("numFrames", type=float),
        TclMember("numSA", type=int),
        TclMember("pattern"),
        TclMember("patternType"),
        TclMember("percentPacketRate", type=float),
        TclMember("preambleData"),
        TclMember("preambleSize", type=int),
        TclMember("priorityGroup", type=int),
        TclMember("rateMode"),
        TclMember("returnToId", type=int),
        TclMember("rxTriggerEnable"),
        TclMember("sa", type=MacStr),
        TclMember("saMaskSelect"),
        TclMember("saMaskValue", type=MacStr),
        TclMember("saRepeatCounter"),
        TclMember("saStep", type=int),
        TclMember("sourceInterfaceDescription"),
        TclMember("startTxDelayUnit"),
        TclMember("startTxDelay"),
    ]

    __tcl_commands__ = ["export", "write"]

    next_group_id = 0

    def __init__(self, parent, uri):
        super().__init__(parent=parent, uri=uri.replace("/", " "))
        self.rx_ports = []

    def create(self, name: str) -> None:
        self.ix_set_default()
        self.protocol.ix_set_default()
        self.vlan.ix_set_default()
        if not name:
            name = self.obj_name()
        self.name = "{" + name.replace("%", "%%").replace("\\", "\\\\") + "}"
        self.ix_set()
        self.packetGroup.groupId = IxeStream.next_group_id
        IxeStream.next_group_id += 1

    def remove(self) -> None:
        self.ix_command("remove")
        self.ix_command("write")
        self.del_object_from_parent()

    def ix_set_default(self) -> None:
        super().ix_set_default()
        for stream_object in [o for o in self.__dict__.values() if isinstance(o, IxeStreamObj)]:
            stream_object.ix_set_default()

    def read_stats(self, *stats):
        return IxeStreamsStats(self).read_stats(*stats)[str(self)]

    #
    # Stream objects.
    #

    def _set_ip(self, version):
        require_set = False
        if self.protocol.ethernetType == "0":
            self.protocol.ethernetType = "ethernetII"
            require_set = True
        if self.protocol.name == "0":
            # for some reason (bug?) alias (ip/ipv4) is not acceptable here.
            self.protocol.name = str(version)
            require_set = True
        if require_set and not IxeObject.get_auto_set():
            self.ix_set()

    def get_ip(self):
        self._set_ip(4)
        return self._get_object("_ip", IxeIp)

    ip = property(get_ip)

    def get_ipV6(self):
        self._set_ip(31)
        return self._get_object("_ipV6", IxeIpv6)

    ipV6 = property(get_ipV6)

    def get_tcp(self):
        return self._get_object("_tcp", IxeTcp)

    tcp = property(get_tcp)

    def get_udp(self):
        return self._get_object("_udp", IxeUdp)

    udp = property(get_udp)

    def get_protocol(self):
        return self._get_object("_protocol", IxeProtocol)

    protocol = property(get_protocol)

    def get_protocolOffset(self):
        return self._get_object("_protocolOffset", IxeProtocolOffset)

    protocolOffset = property(get_protocolOffset)

    def get_weightedRandomFramesize(self):
        return self._get_object("_weightedRandomFramesize", IxeWeightedRandomFramesize)

    weightedRandomFramesize = property(get_weightedRandomFramesize)

    def get_udf(self):
        return self._get_object("_udf", IxeUdf)

    udf = property(get_udf)

    def get_dataIntegrity(self):
        return self._get_object("_dataIntegrity", IxeDataIntegrityStream)

    dataIntegrity = property(get_dataIntegrity)

    def get_packetGroup(self):
        return self._get_object("_packetGroup", IxePacketGroupStream)

    packetGroup = property(get_packetGroup)

    def get_autoDetectInstrumentation(self):
        return self._get_object("_autoDetectInstrumentation", IxeAutoDetectInstrumentationStream)

    autoDetectInstrumentation = property(get_autoDetectInstrumentation)

    def get_vlan(self):
        return self._get_object("_vlan", IxeVlan)

    vlan = property(get_vlan)

    def get_stacked_vlan(self):
        return self._get_object("_stackedVlan", IxeStackedVlan)

    stackedVlan = property(get_stacked_vlan)


#
# Stream object classes.
#


class IxeStreamObj(IxeObjectObj):
    def __init__(self, parent, uri=None):
        super().__init__(parent=parent, uri=uri if uri else " ".join(parent.uri.split()[:-1]))

    def ix_command(self, command, *args, **kwargs):
        rc = self.api.call(("{} {}" + len(args) * " {}").format(self.__tcl_command__, command, *args))
        self.ix_set()
        return rc


class IxeProtocol(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "protocol"
    __tcl_members__ = [
        TclMember("appName"),
        TclMember("ethernetType"),
        TclMember("enable802dot1qTag", type=int),
        TclMember("name"),
    ]

    def ix_get(self, member=None, force=False):
        self.parent.ix_get(member, force)

    def ix_set(self, member=None):
        self.parent.ix_set(member)


class IxeVlan(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "vlan"
    __tcl_members__ = [
        TclMember("cfi", type=int),
        TclMember("maskval"),
        TclMember("mode"),
        TclMember("name", flags=FLAG_RDONLY),
        TclMember("repeat", type=int),
        TclMember("step", type=int),
        TclMember("userPriority", type=int),
        TclMember("vlanID", type=int),
        TclMember("protocolTagId"),
    ]
    __tcl_commands__ = ["setDefault"]


class IxeStackedVlan(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "stackedVlan"
    __tcl_members__ = [
        TclMember("numVlans", flags=FLAG_RDONLY),
    ]
    __tcl_commands__ = ["setDefault", "addVlan", "delVlan", "getFirstVlan", "getNextVlan", "getVlan", "setVlan"]


class IxeIp(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "ip"
    __tcl_members__ = [
        TclMember("assuredForwardingClass", type=int),
        TclMember("assuredFowardingPrecedence", type=int),
        TclMember("checksum"),
        TclMember("classSelector", type=int),
        TclMember("cost", type=int),
        TclMember("delay", type=int),
        TclMember("destClass", type=int),
        TclMember("destIpAddr"),
        TclMember("destIpAddrMode"),
        TclMember("destIpAddrRepeatCount", type=int),
        TclMember("destIpMask"),
        TclMember("dscpMode", type=int),
        TclMember("dscpValue"),
        TclMember("enableDestSyncFromPpp", type=bool),
        TclMember("enableHeaderLengthOverride", type=bool),
        TclMember("enableSourceSyncFromPpp", type=bool),
        TclMember("fragment", type=int),
        TclMember("fragmentOffset", type=int),
        TclMember("headerLength"),
        TclMember("identifier", type=int),
        TclMember("ipProtocol", type=int),
        TclMember("lastFragment", type=int),
        TclMember("lengthOverride", type=bool),
        TclMember("options"),
        TclMember("precedence", type=int),
        TclMember("qosMode", type=int),
        TclMember("reliability", type=int),
        TclMember("reserved", type=int),
        TclMember("sourceCommand", type=int),
        TclMember("sourceIpAddr"),
        TclMember("sourceIpAddrMode"),
        TclMember("sourceIpAddrRepeatCount", type=int),
        TclMember("sourceIpMask"),
        TclMember("throughput", type=int),
        TclMember("totalLength", type=int),
        TclMember("ttl", type=int),
        TclMember("useValidChecksum"),
    ]


class IxeIpv6(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "ipV6"
    __tcl_members__ = [
        TclMember("destAddr"),
        TclMember("destAddrMode"),
        TclMember("destAddrRepeatCount", type=int),
        TclMember("destMask", type=int),
        TclMember("destStepSize", type=int),
        TclMember("flowLabel", type=int),
        TclMember("hopLimit", type=int),
        TclMember("nextHeader", type=int),
        TclMember("sourceAddr"),
        TclMember("sourceAddrMode"),
        TclMember("sourceAddrRepeatCount", type=int),
        TclMember("sourceMask", type=int),
        TclMember("sourceStepSize", type=int),
        TclMember("trafficClass", type=int),
    ]
    __tcl_commands__ = [
        "addExtensionHeader",
        "clearAllExtensionHeaders",
        "config",
        "decode",
        "delExtensionHeader",
        "getFirstExtensionHeader",
        "getNextExtensionHeader",
        "setDefault",
    ]


class IxeTcp(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "tcp"
    __tcl_members__ = [
        TclMember("acknowledgementNumber"),
        TclMember("acknowledgeValid"),
        TclMember("checksum"),
        TclMember("destPort"),
        TclMember("finished"),
        TclMember("offset"),
        TclMember("pushFunctionValid"),
        TclMember("resetConnection"),
        TclMember("sequenceNumber"),
        TclMember("sourcePort"),
        TclMember("synchronize"),
        TclMember("urgentPointer"),
        TclMember("urgentPointerValid"),
        TclMember("useValidChecksum"),
        TclMember("window"),
    ]


class IxeUdp(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "udp"
    __tcl_members__ = [
        TclMember("checksum"),
        TclMember("checksumMode"),
        TclMember("destPort"),
        TclMember("enableChecksumOverride"),
        TclMember("enableChecksum"),
        TclMember("length"),
        TclMember("lengthOverride"),
        TclMember("sourcePort"),
    ]


class IxeProtocolOffset(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "protocolOffset"
    __tcl_members__ = [
        TclMember("offset"),
        TclMember("userDefinedTag"),
    ]


class IxeWeightedRandomFramesize(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "weightedRandomFramesize"
    __tcl_members__ = [
        TclMember("center", type=float),
        TclMember("pairList", flags=FLAG_RDONLY),
        TclMember("randomType", type=int),
        TclMember("weight", type=int),
        TclMember("widthAtHalf", type=float),
    ]
    __tcl_commands__ = ["addPair", "delPair", "updateQuadGaussianCurve"]


class IxeUdf(IxeStreamObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "udf"
    __tcl_members__ = [
        TclMember("bitOffset", type=int),
        TclMember("cascadeType", type=int),
        TclMember("chainFrom", type=int),
        TclMember("continuousCount"),
        TclMember("counterMode", type=int),
        TclMember("countertype", type=int),
        TclMember("enable"),
        TclMember("enableCascade"),
        TclMember("enableIndexMode"),
        TclMember("enableKillBitMode"),
        TclMember("enableSkipZerosAndOnes"),
        TclMember("initval"),
        TclMember("innerLoop"),
        TclMember("innerRepeat"),
        TclMember("innerStep"),
        TclMember("killBitUDFSize"),
        TclMember("linearCoefficient"),
        TclMember("linearCoefficientEnable"),
        TclMember("linearCoefficientLoopCount0"),
        TclMember("linearCoefficientLoopCount2"),
        TclMember("maskselect"),
        TclMember("maskval"),
        TclMember("offset"),
        TclMember("random"),
        TclMember("repeat", type=int),
        TclMember("skipMaskBits"),
        TclMember("step", type=int),
        TclMember("tripleNestedLoop0Increment"),
        TclMember("udfSize"),
        TclMember("updown", type=int),
        TclMember("valueList"),
        TclMember("valueRepeatCount"),
    ]
    __tcl_commands__ = ["addRange", "clearRangeList", "config", "getFirstRange", "getNextRange", "getRange", "setDefault"]

    def ix_get(self, member=None, force=False):
        pass

    def ix_set(self, member=None):
        pass

    def set(self, index):
        self.api.call_rc("{} {} {}".format(self.__tcl_command__, self.__set_command__, index))


#
# TX stream object classes.
#


class IxeStreamTxObj(IxeStreamObj, metaclass=ixe_obj_meta):
    __get_command__ = "getTx"
    __set_command__ = "setTx"

    def __init__(self, parent):
        super().__init__(parent=parent, uri=parent.uri)


class IxeDataIntegrityStream(IxeStreamTxObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "dataIntegrity"
    __tcl_members__ = [
        TclMember("enableTimestamp", type=bool),
        TclMember("insertSignature", type=bool),
        TclMember("floatingTimestampAndDataIntegrityMode"),
        TclMember("numBytesFromEndOfFrame", type=int),
        TclMember("payloadLength", type=int),
        TclMember("signature"),
        TclMember("signatureOffset", type=int),
    ]


class IxePacketGroupStream(IxeStreamTxObj, metaclass=ixe_obj_meta):
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


class IxeAutoDetectInstrumentationStream(IxeStreamTxObj, metaclass=ixe_obj_meta):
    __tcl_command__ = "autoDetectInstrumentation"
    __tcl_members__ = [
        TclMember("enableMisdirectedPacketMask", type=bool),
        TclMember("enablePRBS", type=bool),
        TclMember("enableSignatureMask", type=bool),
        TclMember("enableTxAutomaticInstrumentation", type=bool),
        TclMember("misdirectedPacketMask"),
        TclMember("signature"),
        TclMember("signatureMask"),
        TclMember("startOfScan", type=int),
    ]
