
from os import path
import re

from trafficgenerator.tgn_utils import TgnError
from trafficgenerator.tgn_tcl import tcl_str
from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY, MacStr
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_stream import IxeStream
from ixexplorer.ixe_statistics_view import IxeCapFileFormat, IxePortsStats, IxeCaptureBuffer


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
        TclMember('dataCenterMode', type=bool),
        TclMember('DestMacAddress', type=MacStr),
        TclMember('directedAddress', type=MacStr),
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

    ]

    __tcl_commands__ = ['export', 'getFeature', 'getStreamCount', 'reset', 'setFactoryDefaults', 'setPhyMode',
                        'setModeDefaults', 'setReceiveMode', 'setTransmitMode', 'setDefault', 'restartAutoNegotiation',
                        'getPortState']

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
        warnings_list = (self.api.call('join ' + tcl_str(stream_warnings) + ' LiStSeP').split('LiStSeP')
                         if self.streamRegion.generateWarningList() else [])
        for warning in warnings_list:
            if warning:
                raise TgnError(warning)

    def load_config(self, config_file_name):
        """ Load configuration file from prt or str.

        Configuration file type is extracted from the file suffix - prt or str.

        :param config_file_name: full path to the configuration file.
        """

        config_file_name = config_file_name.replace('\\', '/')
        ext = path.splitext(config_file_name)[-1].lower()
        if ext == '.prt':
            self.api.call_rc('port import {} {}'.format(config_file_name, self.uri))
        elif ext == '.str':
            self.reset()
            self.api.call_rc('stream import {} {}'.format(config_file_name, self.uri))
        else:
            raise ValueError('Configuration file type {} not supported.'.format(ext))
        self.write()
        self.discover()

    def discover(self):
        self.logger.info('Discover port {}'.format(self.obj_name()))
        for stream_id in range(1, int(self.getStreamCount()) + 1):
            IxeStream(self, self.uri + '/' + str(stream_id))

    def clear_stats(self):
        self.api.call_rc('ixClearPortStats {}'.format(self.uri))
        self.api.call_rc('ixClearPortPacketGroups {}'.format(self.uri))
        self.api.call_rc('ixClearPerStreamTxStats {}'.format(self.session.set_ports_list(self)))

    def add_stream(self, name=None):
        stream = IxeStream(self, self.uri + '/' + str(int(self.getStreamCount()) + 1))
        stream.ix_set_default()
        if not name:
            name = str(stream)
        stream.name = name
        return stream

    def get_streams(self):
        """
        :return: dictionary {stream id: object} of all streams.
        """

        return {int(s.uri[-1]): s for s in self.get_objects_by_type('stream')}
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

    def stop_capture(self, cap_file_name, cap_file_format=IxeCapFileFormat.enc):
        """ Stop capture on port.

        :param cap_file_name: prefix for the capture file name.
            Capture file will be saved as pcap file named 'prefix' + 'URI'.pcap.
        :param cap_file_format: exported file format
        :return: full path to pcap file if capture exists else None
        """

        self.session.stop_capture(cap_file_name, cap_file_format, self)

    def get_cap_file(self):
        return self.session.get_cap_files(self).values()[0]

    def get_cap_frames(self, *frame_nums):
        """ Stop capture on ports.

        :param frame_nums: list of frame numbers to read.
        :return: list of captured frames.
        """

        cap_buffer = IxeCaptureBuffer(parent=self, num_frames=-1)
        frames = []
        for frame_num in frame_nums:
            cap_buffer.getframe(frame_num)
            frames.append(cap_buffer.ix_command('cget', '-frame'))

    def read_stats(self, *stats):
        return IxePortsStats(self.session, self).read_stats(*stats).values()[0]

    def get_dataIntegrity(self):
        return self.get_object('_dataIntegrity', IxeDataIntegrityPort)
    dataIntegrity = property(get_dataIntegrity)

    def get_packetGroup(self):
        return self.get_object('_packetGroup', IxePacketGroupPort)
    packetGroup = property(get_packetGroup)

    def get_streamRegion(self):
        return self.get_object('_streamRegion', IxeStreamRegion)
    streamRegion = property(get_streamRegion)

    def get_object(self, field, ixe_object):
        if not hasattr(self, field):
            setattr(self, field, ixe_object(parent=self))
            getattr(self, field).ix_get()
        return getattr(self, field)


class IxePortObj(IxeObject):

    def __init__(self, parent):
        super(IxePortObj, self).__init__(uri=parent.uri[:-2], parent=parent)

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

    def __init__(self, parent):
        super(IxePortObj, self).__init__(uri=parent.uri, parent=parent)


class IxePacketGroupPort(IxePortObj):
    __tcl_command__ = 'packetGroup'
    __tcl_members__ = [
            TclMember('signature'),
    ]
    __get_command__ = 'getRx'
    __set_command__ = 'setRx'

    def __init__(self, parent):
        super(IxePortObj, self).__init__(uri=parent.uri, parent=parent)


class IxeStreamRegion(IxePortObj):
    __tcl_command__ = 'streamRegion'
    __tcl_members__ = [
    ]
    __tcl_commands__ = ['generateWarningList']

    def __init__(self, parent):
        super(IxePortObj, self).__init__(uri=parent.uri, parent=parent)
