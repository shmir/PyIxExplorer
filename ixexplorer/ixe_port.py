
from os import path
import re
from enum import Enum

from trafficgenerator.tgn_utils import TgnError
from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY, MacStr
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_stream import IxeStream
from ixexplorer.ixe_statistics_view import IxeCapFileFormat, IxePortsStats, IxeStreamsStats


class IxePhyMode(Enum):
    copper = 'portPhyModeCopper'
    fiber = 'portPhyModeFibber'
    ignore = None


class IxeReceiveMode(Enum):
    capture = '$::portCapture'
    packetGroup = '$::portPacketGroup'
    tcpSessions = '$::portRxTcpSessions'
    tcpRoundTrip = '$::portRxTcpRoundTrip'
    dataIntegrity = '$::portRxDataIntegrity'
    firstTimeStamp = '$::portRxFirstTimeStamp'
    sequenceChecking = '$::portRxSequenceChecking'
    bert = '$::portRxModeBert'
    isl = '$::portRxModeIsl'
    bertChannelized = '$::portRxModeBertChannelized'
    echo = '$::portRxModeEcho'
    dcc = '$::portRxModeDcc'
    widePacketGroup = '$::portRxModeWidePacketGroup'
    prbs = '$::portRxModePrbs'
    ratingMonitoring = '$::portRxModeRateMonitoring'
    perFlowErrorStats = '$::portRxModePerFlowErrorStats'


class IxeTransmitMode(Enum):
    packetStreams = 'portTxPacketStreams'
    packetFlows = 'portTxPacketFlows'
    advancedScheduler = 'portTxModeAdvancedScheduler'
    bert = 'portTxModeBert'
    bertChannelized = 'portTxModeBertChannelized'
    echo = 'portTxModeEcho'
    dccStreams = 'portTxModeDccStreams'
    dccAdvancedScheduler = 'portTxModeDccAvancedScheduler'
    dccFlowSpecStreams = 'portTxModeDccFlowsSpeStreams'
    dccFlowSpecAdvancedScheduler = 'portTxModeDccFlowsSpeAdvancedScheduler'
    advancedSchedulerCoarse = 'portTxModeAdvancedSchedulerCoarse'
    streamsCoarse = 'portTxModePacketStreamsCoarse'


class StreamWarningsError(TgnError):
    pass


class IxePort(IxeObject):
    __tcl_command__ = 'port'
    __tcl_members__ = [
        TclMember('advertise1000FullDuplex', type=bool),
        TclMember('advertise100FullDuplex', type=bool),
        TclMember('advertise100HalfDuplex', type=bool),
        TclMember('advertise10FullDuplex', type=bool),
        TclMember('advertise10HalfDuplex', type=bool),
        TclMember('advertiseAbilities'),
        TclMember('autoDetectInstrumentationMode', type=bool),
        TclMember('autonegotiate', type=bool),
        TclMember('dataCenterMode'),
        TclMember('DestMacAddress', type=MacStr),
        TclMember('directedAddress'),
        TclMember('duplex'),
        TclMember('enableAutoDetectInstrumentation', type=bool),
        TclMember('enableDataCenterMode', type=bool),
        TclMember('enableManualAutoNegotiate', type=bool),
        TclMember('enablePhyPolling', type=bool),
        TclMember('enableRepeatableLastRandomPattern', type=bool),
        TclMember('enableSimulateCableDisconnect', type=bool),
        TclMember('enableTransparentDynamicRateChange', type=bool),
        TclMember('enableTxRxSyncStatsMode', type=bool),
        TclMember('flowControl', type=bool),
        TclMember('flowControlType', int),
        TclMember('ignoreLink', type=bool),
        TclMember('linkState', type=int, flags=FLAG_RDONLY),
        TclMember('loopback'),
        TclMember('MacAddress', type=MacStr),
        TclMember('masterSlave', type=bool),
        TclMember('multicastPauseAddress'),
        TclMember('negotiateMasterSlave', type=bool),
        TclMember('operationModeList', type=int),
        TclMember('owner'),
        TclMember('packetFlowFileName'),
        TclMember('pfcEnableValueList'),
        TclMember('pfcEnableValueListBitMatrix'),
        TclMember('pfcResponseDelayEnabled'),
        TclMember('pfcResponseDelayQuanta'),
        TclMember('phyMode', flags=FLAG_RDONLY),
        TclMember('pmaClock', type=int),
        TclMember('portMode', type=int),
        TclMember('preEmphasis'),
        TclMember('receiveMode'),
        TclMember('rxTxMode', type=int),
        TclMember('speed', type=int),
        TclMember('timeoutEnable'),
        TclMember('transmitClockDeviation', type=bool),
        TclMember('transmitClockMode', type=int),
        TclMember('transmitMode', type=int),
        TclMember('txRxSyncInterval', type=int),
        TclMember('type', flags=FLAG_RDONLY),
        TclMember('typeName', flags=FLAG_RDONLY),
        TclMember('usePacketFlowImageFile', type=bool),
        TclMember('enableRsFec', type=bool),
        TclMember('ieeeL1Defaults', type=int),
        TclMember('firecodeRequest', type=int),
        TclMember('firecodeAdvertise', type=int),
        TclMember('firecodeForceOn', type=int),
        TclMember('firecodeForceOff', type=int),
        TclMember('reedSolomonRequest', type=int),
        TclMember('reedSolomonAdvertise', type=int),
        TclMember('reedSolomonForceOn', type=int),
        TclMember('reedSolomonForceOff', type=int)
    ]

    __tcl_commands__ = ['export', 'getFeature', 'getStreamCount', 'reset', 'setFactoryDefaults', 'setModeDefaults',
                        'restartAutoNegotiation', 'getPortState', 'isValidFeature']

    LINK_STATE_DOWN = 0
    LINK_STATE_UP = 1
    LINK_STATE_LOOPBACK = 2
    LINK_STATE_MII_WRITE = 3
    LINK_STATE_RESTART_AUTO = 4
    LINK_STATE_AUTO_NEGOTIATING = 5
    LINK_STATE_MII_FAIL = 6
    LINK_STATE_NO_TRANSCEIVER = 7
    LINK_STATE_INVALID_ADDRESS = 8
    LINK_STATE_READ_LINK_PARTNER = 9
    LINK_STATE_NO_LINK_PARTNER = 10
    LINK_STATE_RESTART_AUTO_END = 11
    LINK_STATE_FPGA_DOWNLOAD_FAILED = 12
    LINK_STATE_LOSS_OF_FRAME = 24
    LINK_STATE_LOSS_OF_SIGNAL = 25

    def __init__(self, parent, uri):
        super(self.__class__, self).__init__(uri=uri.replace('/', ' '), parent=parent)
        self.cap_file_name = None

    def supported_speeds(self):
        return re.findall(r'\d+', self.getFeature('ethernetLineRate'))

    def reserve(self, force=False):
        """ Reserve port.

        :param force: True - take forcefully, False - fail if port is reserved by other user
        """

        if not force:
            try:
                self.api.call_rc('ixPortTakeOwnership {}'.format(self.uri))
            except Exception as _:
                raise TgnError('Failed to take ownership for port {} current owner is {}'.format(self, self.owner))
        else:
            self.api.call_rc('ixPortTakeOwnership {} force'.format(self.uri))

    def release(self):
        self.api.call_rc('ixPortClearOwnership {}'.format(self.uri))

    def write(self):
        self.ix_command('write')
        stream_warnings = self.streamRegion.generateWarningList()
        warnings_list = (self.api.call('join ' + ' {' + stream_warnings + '} ' + ' LiStSeP').split('LiStSeP')
                         if self.streamRegion.generateWarningList() else [])
        for warning in warnings_list:
            if warning:
                raise StreamWarningsError(warning)

    def load_config(self, config_file_name):
        """ Load configuration file from prt or str.

        Configuration file type is extracted from the file suffix - prt or str.

        :param config_file_name: full path to the configuration file.
            IxTclServer must have access to the file location. either:
                The config file is on shared folder.
                IxTclServer run on the client machine.
        """
        config_file_name = config_file_name.replace('\\', '/')
        ext = path.splitext(config_file_name)[-1].lower()
        if ext == '.prt':
            self.api.call_rc('port import "{}" {}'.format(config_file_name, self.uri))
        elif ext == '.str':
            self.reset()
            self.api.call_rc('stream import "{}" {}'.format(config_file_name, self.uri))
        else:
            raise ValueError('Configuration file type {} not supported.'.format(ext))
        self.write()
        self.discover()

    def discover(self):
        self.logger.info('Discover port {}'.format(self.obj_name()))
        for stream_id in range(1, int(self.getStreamCount()) + 1):
            IxeStream(self, self.uri + '/' + str(stream_id))

    def clear_port_stats(self):
        self.api.call_rc('ixClearPortStats {}'.format(self.uri))

    def clear_stats(self):
        self.api.call_rc('ixClearPortStats {}'.format(self.uri))
        self.api.call_rc('ixClearPortPacketGroups {}'.format(self.uri))
        self.api.call_rc('ixClearPerStreamTxStats {}'.format(self.session.set_ports_list(self)))

    def add_stream(self, name=None):
        stream = IxeStream(self, self.uri + '/' + str(int(self.getStreamCount()) + 1))
        stream.ix_set_default()
        if not name:
            name = str(stream)
        stream.name = '{' + name.replace('%', '%%').replace('\\', '\\\\') + '}'
        return stream

    def get_streams(self):
        """
        :return: dictionary {stream id: object} of all streams.
        """

        return {int(s.uri.split()[-1]): s for s in self.get_objects_by_type('stream')}
    streams = property(get_streams)

    def start_transmit(self, blocking=False):
        """ Start transmit on port.

        :param blocking: True - wait for traffic end, False - return after traffic start.
        """

        self.session.start_transmit(blocking, self)

    def stop_transmit(self):
        """ Stop traffic on port. """

        self.session.stop_transmit(self)

    def start_capture(self):
        """ Start capture on port. """

        self.session.start_capture(self)

    def stop_capture(self, cap_file_name=None, cap_file_format=IxeCapFileFormat.mem):
        """ Stop capture on port.

        :param cap_file_name: prefix for the capture file name.
            Capture file will be saved as pcap file named 'prefix' + 'URI'.pcap.
        :param cap_file_format: exported file format
        :return: number of captured frames
        """

        return self.session.stop_capture(cap_file_name, cap_file_format, self)[self]

    def get_cap_file(self):
        return self.session.get_cap_files(self)[self]

    def get_cap_frames(self, *frame_nums):
        """ Stop capture on ports.

        :param frame_nums: list of frame numbers to read.
        :return: list of captured frames.
        """

        frames = []
        for frame_num in frame_nums:
            if self.captureBuffer.getframe(frame_num) == '0':
                frames.append(self.captureBuffer.frame)
            else:
                frames.append(None)
        return frames

    def read_stats(self, *stats):
        return IxePortsStats(self.session, self).read_stats(*stats)[str(self)]

    def read_stream_stats(self, *stats):
        return IxeStreamsStats(self.session, *self.get_objects_by_type('stream')).read_stats(stats)

    def get_filter(self):
        return self.get_object('_filter', IxeFilterPort)
    filter = property(get_filter)

    def get_filterPallette(self):
        return self.get_object('_filterPallette', IxeFilterPalettePort)
    filterPallette = property(get_filterPallette)

    def get_dataIntegrity(self):
        return self.get_object('_dataIntegrity', IxeDataIntegrityPort)
    dataIntegrity = property(get_dataIntegrity)

    def get_packetGroup(self):
        return self.get_object('_packetGroup', IxePacketGroupPort)
    packetGroup = property(get_packetGroup)

    def get_streamRegion(self):
        return self.get_object('_streamRegion', IxeStreamRegion)
    streamRegion = property(get_streamRegion)

    def get_capture(self):
        return self.get_object('_capture', IxeCapture)
    capture = property(get_capture)

    def get_captureBuffer(self):
        return self.get_object('_captureBuffer', IxeCaptureBuffer)
    captureBuffer = property(get_captureBuffer)

    def set_phy_mode(self, mode=IxePhyMode.ignore):
        """ Set phy mode to copper or fiber.

        :param mode: requested PHY mode.
        """

        if mode.value:
            self.api.call_rc('port setPhyMode {} {}'.format(mode.value, self.uri))

    def set_receive_modes(self, *modes):
        """ set port receive mode

        :param modes: requested receive modes
        :type modes: list of ixexplorer.ixe_port.IxeReceiveMode
        """

        mode_values = [mode.value for mode in modes]
        mode_list = "[ expr " + " | ".join(mode_values) + " ]"
        self.api.call_rc('port setReceiveMode {} {}'.format(mode_list, self.uri))

    def set_transmit_mode(self, mode):
        """ set port transmit mode

        :param mode: request transmit mode
        :type mode: ixexplorer.ixe_port.IxeTransmitMode
        """

        self.api.call_rc('port setTransmitMode {} {}'.format(mode, self.uri))

    def get_object(self, field, ixe_object):
        if not hasattr(self, field):
            setattr(self, field, ixe_object(parent=self))
            getattr(self, field).ix_get()
        return getattr(self, field)

    def set_rx_ports(self, *rx_ports):
        for stream in self.get_objects_by_type('stream'):
            stream.rx_ports = rx_ports
    rx_ports = property(fset=set_rx_ports)

    def ix_set_list(self, optList):
        self.ix_get()
        for opt in optList:
            value = optList[opt]
            self.api.call('%s config -%s %s' % (self.__tcl_command__, opt, value))
        self.ix_set()


class IxePortObj(IxeObject):

    def __init__(self, parent):
        super(IxePortObj, self).__init__(uri=parent.uri, parent=parent)

    def ix_get(self, member=None, force=False):
        self.parent.ix_get(member, force)
        super(IxePortObj, self).ix_get(member, force)

    def ix_set(self, member=None):
        super(IxePortObj, self).ix_set(member)
        self.parent.ix_set(member)


class IxeDataIntegrityPort(IxePortObj):
    __tcl_command__ = 'dataIntegrity'
    __tcl_members__ = [
            TclMember('enableTimeStamp'),
            TclMember('insertSignature'),
            TclMember('signature'),
            TclMember('signatureOffset'),
    ]
    __get_command__ = 'getRx'
    __set_command__ = 'setRx'
    __tcl_commands__ = ['config', 'getCircuitRx', 'getQueueRx', 'setCircuitRx', 'setQueueRx']


class IxePacketGroupPort(IxePortObj):
    __tcl_command__ = 'packetGroup'
    __tcl_members__ = [
            TclMember('signature'),
    ]
    __get_command__ = 'getRx'
    __set_command__ = 'setRx'


class IxeFilterPort(IxePortObj):
    __tcl_command__ = 'filter'
    __tcl_members__ = [
            TclMember(''),
            TclMember('captureTriggerDA'),
            TclMember('captureTriggerSA'),
            TclMember('captureTriggerPattern'),
            TclMember('captureTriggerError'),
            TclMember('captureTriggerFrameSizeEnable'),
            TclMember('captureTriggerFrameSizeFrom'),
            TclMember('captureTriggerFrameSizeTo'),
            TclMember('captureTriggerCircuit'),
            TclMember('captureFilterDA'),
            TclMember('captureFilterSA'),
            TclMember('captureFilterPattern'),
            TclMember('captureFilterError'),
            TclMember('captureFilterFrameSizeEnable'),
            TclMember('captureFilterFrameSizeFrom'),
            TclMember('captureFilterFrameSizeTo'),
            TclMember('captureFilterCircuit'),
            TclMember('userDefinedStat1DA'),
            TclMember('userDefinedStat1SA'),
            TclMember('userDefinedStat1Pattern'),
            TclMember('userDefinedStat1Error'),
            TclMember('userDefinedStat1FrameSizeEnable'),
            TclMember('userDefinedStat1FrameSizeFrom'),
            TclMember('userDefinedStat1FrameSizeTo'),
            TclMember('userDefinedStat1Circuit'),
            TclMember('userDefinedStat2DA'),
            TclMember('userDefinedStat2SA'),
            TclMember('userDefinedStat2Pattern'),
            TclMember('userDefinedStat2Error'),
            TclMember('userDefinedStat2FrameSizeEnable'),
            TclMember('userDefinedStat2FrameSizeFrom'),
            TclMember('userDefinedStat2FrameSizeTo'),
            TclMember('userDefinedStat2Circuit'),
            TclMember('asyncTrigger1DA'),
            TclMember('asyncTrigger1SA'),
            TclMember('asyncTrigger1Pattern'),
            TclMember('asyncTrigger1Error'),
            TclMember('asyncTrigger1FrameSizeEnable'),
            TclMember('asyncTrigger1FrameSizeFrom'),
            TclMember('asyncTrigger1FrameSizeTo'),
            TclMember('asyncTrigger1Circuit'),
            TclMember('asyncTrigger2DA'),
            TclMember('asyncTrigger2SA'),
            TclMember('asyncTrigger2Pattern'),
            TclMember('asyncTrigger2Error'),
            TclMember('asyncTrigger2FrameSizeEnable'),
            TclMember('asyncTrigger2FrameSizeFrom'),
            TclMember('asyncTrigger2FrameSizeTo'),
            TclMember('asyncTrigger2Circuit'),
            TclMember('captureTriggerEnable'),
            TclMember('captureFilterEnable'),
            TclMember('userDefinedStat1Enable'),
            TclMember('userDefinedStat2Enable'),
            TclMember('asyncTrigger1Enable'),
            TclMember('asyncTrigger2Enable'),
            TclMember('userDefinedStat1PatternExpressionEnable'),
            TclMember('userDefinedStat2PatternExpressionEnable'),
            TclMember('captureTriggerPatternExpressionEnable'),
            TclMember('captureFilterPatternExpressionEnable'),
            TclMember('asyncTrigger1PatternExpressionEnable'),
            TclMember('asyncTrigger2PatternExpressionEnable'),
            TclMember('userDefinedStat1PatternExpression'),
            TclMember('userDefinedStat2PatternExpression'),
            TclMember('captureTriggerPatternExpression'),
            TclMember('captureFilterPatternExpression'),
            TclMember('asyncTrigger1PatternExpression'),
            TclMember('asyncTrigger2PatternExpression'),
    ]


class IxeStreamRegion(IxePortObj):
    __tcl_command__ = 'streamRegion'
    __tcl_commands__ = ['generateWarningList']


class IxeFilterPalettePort(IxePortObj):
    __tcl_command__ = 'filterPallette'
    __tcl_members__ = [
        TclMember('DA1'),
        TclMember('DAMask1'),
        TclMember('DA2'),
        TclMember('DAMask2'),
        TclMember('SA1'),
        TclMember('SAMask1'),
        TclMember('SA2'),
        TclMember('SAMask2'),
        TclMember('pattern1'),
        TclMember('patternMask1'),
        TclMember('pattern2'),
        TclMember('patternMask2'),
        TclMember('patternOffset1', type=int),
        TclMember('patternOffset2', type=int),
    ]


class IxeCapture(IxePortObj):
    __tcl_command__ = 'capture'
    __tcl_members__ = [
            TclMember('afterTriggerFilter'),
            TclMember('beforeTriggerFilter'),
            TclMember('captureMode'),
            TclMember('continuousFilter'),
            TclMember('enableSmallPacketCapture'),
            TclMember('fullAction'),
            TclMember('nPackets', type=int, flags=FLAG_RDONLY),
            TclMember('sliceSize'),
            TclMember('triggerPosition')
    ]


class IxeCaptureBuffer(IxeObject):
    __tcl_command__ = 'captureBuffer'
    __tcl_members__ = [
            TclMember('frame', flags=FLAG_RDONLY),
    ]
    __tcl_commands__ = ['export', 'getframe']

    def __init__(self, parent):
        super(self.__class__, self).__init__(uri=parent.uri, parent=parent)
        self.api.call_rc('captureBuffer get {} 1 {}'.format(self.uri, self.parent.capture.nPackets))

    def ix_command(self, command, *args, **kwargs):
        return self.api.call(('captureBuffer {} ' + len(args) * ' {}').format(command, *args))

    def ix_get(self, member=None, force=False):
        pass
