import time
from os import path
import re
from enum import Enum
from pathlib import Path
from datetime import datetime

from trafficgenerator.tgn_utils import TgnError
from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY, MacStr, FLAG_IGERR, ixe_obj_meta
from ixexplorer.ixe_object import IxeObject, IxeObjectObj
from ixexplorer.ixe_stream import IxeStream
from ixexplorer.ixe_statistics_view import IxeCapFileFormat, IxePortsStats, IxeStreamsStats, IxeStat


class IxePhyMode(Enum):
    copper = 'portPhyModeCopper'
    fiber = 'portPhyModeFibber'
    sgmii = 'portPhyModeSgmii'
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
    __tcl_command__ = 'port'
    __tcl_members__ = [
        TclMember('advertise2P5FullDuplex', type=int, flags=FLAG_IGERR),
        TclMember('advertise5FullDuplex', type=int, flags=FLAG_IGERR),
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
        TclMember('masterSlave'),
        TclMember('multicastPauseAddress'),
        TclMember('negotiateMasterSlave', type=bool),
        TclMember('operationModeList'),
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
        TclMember('receiveMode', type=int),
        TclMember('rxTxMode', type=int),
        TclMember('speed', type=int),
        TclMember('timeoutEnable'),
        TclMember('transmitClockDeviation', type=bool),
        TclMember('transmitClockMode', type=int),
        TclMember('transmitMode'),
        TclMember('txRxSyncInterval', type=int),
        TclMember('type', flags=FLAG_RDONLY),
        TclMember('typeName', flags=FLAG_RDONLY),
        TclMember('usePacketFlowImageFile', type=bool),
        TclMember('enableRsFec', type=bool),
        TclMember('ieeeL1Defaults', type=int, flags=FLAG_IGERR),
        TclMember('enableFramePreemption', type=bool, flags=FLAG_IGERR),
        TclMember('enableSmdVRExchange', type=bool, flags=FLAG_IGERR),
        TclMember('reedSolomonForceOn', type=bool, flags=FLAG_IGERR),
    ]

    __tcl_commands__ = ['export', 'getFeature', 'getStreamCount', 'reset', 'setFactoryDefaults', 'setModeDefaults',
                        'restartAutoNegotiation', 'getPortState', 'isValidFeature', 'isActiveFeature',
                        'isCapableFeature']

    mode_2_speed = {'0': '10000',
                    '5': '100000',
                    '6': '40000',
                    '7': '100000',
                    '8': '40000',
                    '9': '10000',
                    '10': '10000',
                    '18': '25000',
                    '19': '50000',
                    '20': '25000'}

    def __init__(self, parent, uri):
        super().__init__(parent=parent, uri=uri.replace('/', ' '))
        self.cap_file_name = None
        self.cap_stop_frame = None

    def supported_speeds(self):
        # todo FIX  once parent is Session(by reserve_ports) - no active_ports ,only if parent is card(by discover)!!!
        # if self.parent.active_ports == self.parent.ports:
        supported_speeds = re.findall(r'\d+', self.getFeature('ethernetLineRate'))
        # Either active_ports != self.parent.ports or empty supported speeds for whatever reason...
        if not supported_speeds:
            for rg in self.parent.resource_groups.values():
                if self.index in rg.active_ports:
                    speed = rg.mode if int(rg.mode) >= 1000 else self.mode_2_speed.get(rg.mode, rg.mode)
                    supported_speeds = [speed]
                    break
        return supported_speeds

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
        """ Release port. """
        self.api.call_rc('ixPortClearOwnership {}'.format(self.uri))

    def write_config(self):
        self.session.write_config(self)
        stream_warnings = self.streamRegion.generateWarningList()
        warnings_list = (self.api.call('join ' + ' {' + stream_warnings + '} ' + ' LiStSeP').split('LiStSeP')
                         if self.streamRegion.generateWarningList() else [])
        for warning in warnings_list:
            if warning:
                raise StreamWarningsError(warning)

    def write(self):
        """ Write configuration to chassis.

        Raise StreamWarningsError if configuration warnings found.
        """

        self.ix_command('write')
        stream_warnings = self.streamRegion.generateWarningList()
        warnings_list = (self.api.call('join ' + ' {' + stream_warnings + '} ' + ' LiStSeP').split('LiStSeP')
                         if self.streamRegion.generateWarningList() else [])
        for warning in warnings_list:
            if warning:
                raise StreamWarningsError(warning)

    def clear(self, phy_mode=IxePhyMode.ignore):
        self.ix_set_default()
        self.setFactoryDefaults()
        self.set_phy_mode(phy_mode)
        self.reset()
        self.clear_port_stats()
        self.write()
        self.clear_all_stats()
        self.del_objects_by_type('stream')

    def load_config(self, config_file_name):
        """ Load configuration file from prt or str.

        Configuration file type is extracted from the file suffix - prt or str.

        :param config_file_name: full path to the configuration file.
            IxTclServer must have access to the file location. either:
                The config file is on shared folder.
                IxTclServer run on the client machine.
        """
        config_file_name = Path(config_file_name)
        ext = config_file_name.suffix
        if ext == '.prt':
            self.api.call_rc(f'port import "{config_file_name.as_posix()}" {self.uri}')
        elif ext == '.str':
            self.reset()
            self.api.call_rc(f'stream import "{config_file_name.as_posix()}" {self.uri}')
        else:
            raise ValueError(f'Configuration file type {ext} not supported.')
        self.write()
        self.discover()

    def save_config(self, config_file_name):
        """ Save configuration file from prt or str.

        Configuration file type is extracted from the file suffix - prt or str.

        :param config_file_name: full path to the configuration file.
            IxTclServer must have access to the file location. either:
                The config file is on shared folder.
                IxTclServer run on the client machine.
        """
        config_file_name = Path(config_file_name)
        ext = config_file_name.suffix
        if ext == '.prt':
            self.api.call_rc(f'port export "{config_file_name}" {self.uri}')
        elif ext == '.str':
            self.api.call_rc(f'stream export "{config_file_name}" {self.uri}')
        else:
            raise ValueError(f'Configuration file type {ext} not supported.')

    def wait_for_up(self, timeout=16):
        """ Wait until port is up and running.

        :param timeout: seconds to wait.
        """

        self.session.wait_for_up(timeout, [self])

    def discover(self):
        self.logger.info('Discover port {}'.format(self.obj_name()))
        self.ix_get()
        for stream_id in range(1, int(self.getStreamCount()) + 1):
            IxeStream(self, self.uri + '/' + str(stream_id))

    def start_transmit(self, blocking=False):
        """ Start transmit on port.

        :param blocking: True - wait for traffic end, False - return after traffic start.
        """

        self.session.start_transmit(blocking, False, self)

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
        tmStamps = []
        self.cap_stop_frame = max(frame_nums)
        for frame_num in frame_nums:
            if self.captureBuffer.getframe(frame_num) == '0':
                frames.append(self.captureBuffer.frame)
                secs = int(self.captureBuffer.timestamp)/1e9
                dt = datetime.fromtimestamp(secs)
                x = dt.strftime('%H:%M:%S.%f')
                tmStamps.append(x)
            else:
                frames.append(None)
        return frames,tmStamps

    #IxRouter

    def init_interface_table(self):
        self.interfaceTable.ix_command('select')
        self.interfaceTable._command('clearAllInterfaces')

    #
    # Statistics.
    #

    def clear_port_stats(self):
        """ Clear only port stats (leave stream and packet group stats).

        Do not use - still working with Ixia to resolve.
        """
        stat = IxeStat(self)
        stat.ix_set_default()
        stat.enableValidStats = True
        stat.ix_set()
        stat.write()

    def clear_all_stats(self):
        """ Clear all statistic counters (port, streams and packet groups) on list of ports. """
        self.session.clear_all_stats(self)

    def read_stats(self, *stats):
        return IxePortsStats(self).read_stats(*stats)[str(self)]

    def read_stream_stats(self, *stats):
        return IxeStreamsStats(*self.get_objects_by_type('stream')).read_stats(*stats)

    def reset_sequence_index(self):
        self.api.call_rc('ixResetPortSequenceIndex {}'.format(self.uri))

    #
    # Others...
    #

    def set_phy_mode(self, mode=IxePhyMode.ignore):
        """ Set phy mode to copper or fiber.
        :param mode: requested PHY mode.
        """
        if isinstance(mode, IxePhyMode):
            if mode.value:
                self.api.call_rc('port setPhyMode {} {}'.format(mode.value, self.uri))
        else:
            self.api.call_rc('port setPhyMode {} {}'.format(mode, self.uri))

    def set_receive_modes(self, *modes):
        """ Set port receive modes (overwrite existing value).

        :param modes: requested receive modes
        :type modes: list[ixexplorer.ixe_port.IxeReceiveMode]
        """

        self._set_receive_modes(0, *modes)

    def add_receive_modes(self, *modes):
        """ Add port receive modes to exiting modes.

        :param modes: requested receive modes
        :type modes: list[ixexplorer.ixe_port.IxeReceiveMode]
        """

        self._set_receive_modes(self.receiveMode, *modes)

    def set_transmit_mode(self, mode):
        """ set port transmit mode

        :param mode: request transmit mode
        :type mode: ixexplorer.ixe_port.IxeTransmitMode
        """

        self.api.call_rc('port setTransmitMode {} {}'.format(mode, self.uri))

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

    def set_wide_packet_group(self):
        self.set_receive_modes(IxeReceiveMode.widePacketGroup, IxeReceiveMode.dataIntegrity)

    def add_stream(self, name=None):
        stream = IxeStream(self, f'{self.uri} {str(int(self.getStreamCount()) + 1)}')
        stream.create(name)
        return stream

    #
    # Port objects.
    #

    def get_autoDetectInstrumentation(self):
        return self._get_object('_autoDetectInstrumentation', IxeAutoDetectInstrumentationPort)
    autoDetectInstrumentation = property(get_autoDetectInstrumentation)

    def get_capture(self):
        return self._get_object('_capture', IxeCapture)
    capture = property(get_capture)

    def get_captureBuffer(self):
        return self._get_object('_captureBuffer', IxeCaptureBuffer)

    def set_captureBuffer(self, value):
        self._captureBuffer = value
    captureBuffer = property(fget=get_captureBuffer, fset=set_captureBuffer)

    def get_dataIntegrity(self):
        return self._get_object('_dataIntegrity', IxeDataIntegrityPort)
    dataIntegrity = property(get_dataIntegrity)

    def get_filter(self):
        return self._get_object('_filter', IxeFilterPort)
    filter = property(get_filter)

    def get_filterPallette(self):
        return self._get_object('_filterPallette', IxeFilterPalettePort)
    filterPallette = property(get_filterPallette)

    def get_packetGroup(self):
        return self._get_object('_packetGroup', IxePacketGroupPort)
    packetGroup = property(get_packetGroup)

    def get_splitPacketGroup(self):
        return self._get_object('_splitPacketGroup', IxeSplitPacketGroup)
    splitPacketGroup = property(get_splitPacketGroup)

    def get_streamRegion(self):
        return self._get_object('_streamRegion', IxeStreamRegion)
    streamRegion = property(get_streamRegion)

    def get_arpServer(self):
        return self._get_object('_arpServer', IxeArpServer)
    arpServer = property(get_arpServer)

    def get_interfaceTable(self):
        return self._get_object('_interfaceTable', IxeInterfaceTable)
    interfaceTable = property(get_interfaceTable)

    def get_protocolServer(self):
        return self._get_object('_protocolServer', IxeProtocolServer)
    protocolServer = property(get_protocolServer)

    def get_interfaceEntry(self):
        return self._get_object('_interfaceEntry', IxeInterfaceEntry)
    interfaceEntry = property(get_interfaceEntry)

    def get_interfaceIpV4(self):
        return self._get_object('_interfaceIpV4', IxeInterfaceIpV4)
    interfaceIpV4 = property(get_interfaceIpV4)

    def get_interfaceDhcpV4(self):
        return self._get_object('_interfaceDhcpV4', IxeInterfaceDhcpV4)
    interfaceDhcpV4 = property(get_interfaceDhcpV4)

    def get_interfaceIpV6(self):
        return self._get_object('_interfaceIpV6', IxeInterfaceIpV6)
    interfaceIpV6 = property(get_interfaceIpV6)

    #
    # Properties.
    #

    def get_streams(self):
        """
        :return: dictionary {stream id: object} of all streams.
        """

        return {int(s.index): s for s in self.get_objects_by_type('stream')}
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


class IxePortObj(IxeObjectObj, metaclass=ixe_obj_meta):

    def __init__(self, parent):
        super().__init__(parent=parent, uri=parent.uri)


class IxeArpServer(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'arpServer'
    __tcl_members__ = [
        TclMember('retries', type=int),
        TclMember('mode', type=int),
        TclMember('rate', type=int),
        TclMember('requestRepeatCount', type=int)
    ]



class IxeInterfaceTable(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'interfaceTable'
    __tcl_members__ = [
        TclMember('dhcpV4RequestRate', type=int),
        TclMember('dhcpV6RequestRate', type=int),
        TclMember('dhcpV4MaximumOutstandingRequests', type=int),
        TclMember('dhcpV6MaximumOutstandingRequests', type=int),
        TclMember('fcoeRequestRate'),
        TclMember('fcoeNumRetries', type=int),
        TclMember('fcoeRetryInterval', type=int),
        TclMember('fipVersion'),
        TclMember('enableFcfMac', type=bool),
        TclMember('fcfMacCollectionTime', type=int),
        TclMember('enablePMacInFpma', type=bool),
        TclMember('enableNameIdInVLANDiscovery', type=bool),
        TclMember('enableTargetLinkLayerAddrOption', type=bool),
        TclMember('enableAutoNeighborDiscovery', type=bool),
        TclMember('enableAutoArp', type=bool)
    ]

    __tcl_commands__ = ['select', 'clearAllInterfaces', 'addInterface', 'delInterface', 'getInterface', 'getFcoeDiscoveredInfo',
                        'getFirstInterface', 'getNextInterface', 'sendRouterSolicitation', 'clearDiscoveredNeighborTable',
                        'sendNeighborClear','sendNeighborRefresh','sendNeighborSolicitation'
                        'sendArp', 'sendArpClear', 'sendArpRefresh','setInterface',
                        'requestDiscoveredTable','getDiscoveredList','ping']

    def select(self):
        self.ix_command('select')

    def _raw_command(self,ix_command, command, *args, **kwargs):
        return self.api.call((ix_command+' {} ' + len(args) * ' {}').format(command, *args))

    def _command(self, command, *args, **kwargs):
        return self._raw_command('interfaceTable',command, *args, **kwargs)

    def _discover_list_command(self, command, *args, **kwargs):
        return self._raw_command('discoveredList', command, *args, **kwargs)

    def _get_discovered_address(self, command='cget -ipAddress', *args, **kwargs):
        return self._raw_command('discoveredAddress', command, *args, **kwargs)

    def _discover_neighbor_command(self, command, *args, **kwargs):
        return self._raw_command('discoveredNeighbor', command, *args, **kwargs)

    def _discover_dhcp_command(self, command='cget -ipAddress', *args, **kwargs):
        return self._raw_command('dhcpV4DiscoveredInfo', command, *args, **kwargs)

    def add_if(self):
        self._command('addInterface')

    def send_ping(self,if_name,dest_ip):
        params = [if_name,'addressTypeIpV4',dest_ip]
        self.select()
        self._command('ping', *params)

    def send_request_discovered_table(self, if_name=None):
        self._command('requestDiscoveredTable')

    def send_get_discovered_list(self, if_name=None):
        if if_name:
            return self._command('getDiscoveredList',if_name)
        else:
            return self._command('getDiscoveredList')

    def send_get_discovered_dhcp(self, if_name=None):
        if if_name:
            return self._command('getDhcpV4DiscoveredInfo', if_name)
        else:
            return self._command('getDhcpV4DiscoveredInfo')

    def ix_get(self, member=None, force=False):
        pass

    def ix_set(self, member=None, force=False):
        self._command('set')

    def init(self):
        self.select()
        self._command('clearAllInterfaces')

    def send_RS(self, if_name=None):
        self.select()
        if if_name:
            self._command('sendRouterSolicitation', if_name)
        else:
            self._command('sendRouterSolicitation')

    def send_NS(self):
        self.select()
        self._command('sendNeighborSolicitation')

    def send_NS_clear(self):
        self.select()
        self._command('sendNeighborClear')

    def send_NS_refresh(self):
        self.select()
        self._command('sendNeighborRefresh')

    def send_arp(self, if_name=None):
        self.select()
        if if_name:
            self._command('sendArp', if_name)
        else:
            self._command('sendArp')

    def send_arp_clear(self, if_name=None):
        self.select()
        if if_name:
            self._command('sendArpClear', if_name)
        else:
            self._command('sendArpClear')

    def send_arp_refresh(self, if_name=None):
        self.select()
        if if_name:
            self._command('sendArpRefresh', if_name)
        else:
            self._command('sendArpRefresh')

    def read_if_dhcp(self, if_name=None):
        dhcp_info = {}
        self.select()
        if self._command('getFirstInterface') == '0':
            desc = '{'+self._raw_command('interfaceEntry','cget -description')+'}'
            if not if_name or desc.count(if_name) > 0:
                dhcp_info[desc] = self.read_dhcp_info(desc)
            while self._command('getNextInterface') == '0':
                desc = '{'+self._raw_command('interfaceEntry', 'cget -description')+'}'
                if not if_name or desc.count(if_name) > 0:
                    dhcp_info[desc] = self.read_dhcp_info(desc)
        return dhcp_info

    def read_dhcp_info(self, if_name):
        res = []

        def get_dhcp():
            ip = self._discover_dhcp_command('cget -ipAddress')
            gw = self._discover_dhcp_command('cget -gatewayIpAddress')
            px = self._discover_dhcp_command('cget -prefixLength')
            lease = self._discover_dhcp_command('cget -leaseDuration')
            print(f"ipAddress:{ip},gatewayIpAddress:{gw},prefixLength{px},leaseDuration{lease}")
            return ip, gw, px, lease
        time.sleep(2)
        self.send_request_discovered_table()
        time.sleep(2)
        ack = self.send_get_discovered_dhcp(if_name)
        res = get_dhcp() if ack == '0' else None
        print(f"interface: {if_name} DISCOVERED DHCP : {res}")
        return res


    def read_port_neighbors(self, if_name=None):
        discovered_neighbors = {}
        self.select()
        if self._command('getFirstInterface') == '0':
            desc = '{'+self._raw_command('interfaceEntry','cget -description')+'}'
            if not if_name or desc.count(if_name) > 0:
                discovered_neighbors[desc] = self._read_if_neighbors()
            while self._command('getNextInterface') == '0':
                desc = '{'+self._raw_command('interfaceEntry','cget -description')+'}'
                if not if_name or desc.count(if_name) > 0:
                    discovered_neighbors[desc] = self._read_if_neighbors()
        return discovered_neighbors

    def _read_if_neighbors(self):
        res = []
        def get_mac_ip():
            mac = self._discover_neighbor_command('cget -macAddress')
            ip = self._get_discovered_address()
            return mac, ip
        def read_neighbor_content():
            mac_ip_list = []
            if self._discover_neighbor_command('getFirstAddress') == '0':
                mac_ip_1 = get_mac_ip()
                mac_ip_list.append(mac_ip_1)
                while self._discover_neighbor_command('getNextAddress') == '0':
                    mac_ip_next = get_mac_ip()
                    mac_ip_list.append(mac_ip_next)
            return mac_ip_list

        time.sleep(1)
        self.send_request_discovered_table()
        time.sleep(3)
        self.send_get_discovered_list()
        if self._discover_list_command('getFirstNeighbor') == '0':
            local_res_first = read_neighbor_content()
            res.append(local_res_first)
            while self._discover_list_command('getNextNeighbor') == '0':
                local_res_next = read_neighbor_content()
                res.append(local_res_next)
        return sum(res, [])

class IxeInterfaceEntry(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'interfaceEntry'
    __tcl_members__ = [
        TclMember('enable', type=int),
        TclMember('description'),
        TclMember('macAddress'),
        TclMember('eui64Id', type=int),
        TclMember('mtu', type=int),
        TclMember('enableDhcp', type=int),
        TclMember('enableVlan', type=int),
        TclMember('vlanId'),
        TclMember('vlanPriority'),
        TclMember('vlanTPID'),
        TclMember('enableDhcpV6', type=int),
        TclMember('ipV6Gateway'),
        TclMember('interfaceType', type=int),
    ]
    __tcl_commands__ = ['clearAllItems', 'addItem', 'delItem', 'getFirstItem', 'getNextItem',
                        'getItem']

    def ix_get(self, member=None, force=False):
        pass

    def ix_set(self, member=None, force=False):
        pass

    def _command(self, command, *args, **kwargs):
        return self.api.call(('interfaceEntry {} ' + len(args) * ' {}').format(command, *args))

    def add_item(self, v6=False):
        type = 17 if not v6 else 18
        self._command('addItem', type)

    def clear_all_items(self):
        self._command('clearAllItems', 17)
        self._command('clearAllItems', 18)


class IxeInterfaceIpV4(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'interfaceIpV4'
    __tcl_members__ = [
        TclMember('ipAddress'),
        TclMember('gatewayIpAddress'),
        TclMember('maskWidth', type=int)
    ]

    def ix_get(self, member=None, force=False):
        pass

    def ix_set(self, member=None, force=False):
        pass

class IxeInterfaceDhcpV4(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'dhcpV4Properties'
    __tcl_members__ = [
        TclMember('clientId'),
        TclMember('serverId'),
        TclMember('vendorId'),
        TclMember('renewTimer', type=int),
        TclMember('retryCount', type=int),
    ]

    __tcl_commands__ = ['setDefault', 'removeAllTlvs']

    def ix_get(self, member=None, force=False):
        pass

    def ix_set(self, member=None, force=False):
        pass


class IxeInterfaceIpV6(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'interfaceIpV6'
    __tcl_members__ = [
        TclMember('ipAddress'),
        TclMember('maskWidth', type=int)
    ]

    def ix_get(self, member=None, force=False):
        pass

    def ix_set(self, member=None, force=False):
        pass

class IxeProtocolServer(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'protocolServer'
    __tcl_members__ = [
        TclMember('enableArpResponse', type=int),
        TclMember('enablePingResponse', type=int)
        ]


class IxeCapture(IxePortObj, metaclass=ixe_obj_meta):
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


class IxeCaptureBuffer(IxeObject, metaclass=ixe_obj_meta):
    __tcl_command__ = 'captureBuffer'
    __tcl_members__ = [
        TclMember('frame', flags=FLAG_RDONLY),
        TclMember('timestamp', flags=FLAG_RDONLY),
    ]
    __tcl_commands__ = ['export', 'getframe']

    def __init__(self, parent):
        super().__init__(parent=parent, uri=parent.uri)
        if not self.parent.capture.nPackets:
            return
        packets_to_read = self.parent.capture.nPackets if not self.parent.cap_stop_frame else self.parent.cap_stop_frame
        self.api.call_rc('captureBuffer get {} 1 {}'.format(self.uri, packets_to_read))

    def ix_command(self, command, *args, **kwargs):
        return self.api.call(('captureBuffer {} ' + len(args) * ' {}').format(command, *args))

    def ix_get(self, member=None, force=False):
        pass


class IxeFilterPalettePort(IxePortObj, metaclass=ixe_obj_meta):
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
        TclMember('patternOffset2', type=int)
    ]


class IxeFilterPort(IxePortObj, metaclass=ixe_obj_meta):
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


class IxeSplitPacketGroup(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'splitPacketGroup'
    __tcl_members__ = [
        TclMember('groupIdOffset', type=int),
        TclMember('groupIdOffsetBaseType'),
        TclMember('groupIdWidth', type=int),
        TclMember('groupIdMask')
    ]

    def __init__(self, parent):
        super(self.__class__, self).__init__(parent)
        self.ix_set_default()


class IxeStreamRegion(IxePortObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'streamRegion'
    __tcl_commands__ = ['generateWarningList']


#
# RX port object classes.
#

class IxePortRxObj(IxePortObj, metaclass=ixe_obj_meta):
    __get_command__ = 'getRx'
    __set_command__ = 'setRx'


class IxeAutoDetectInstrumentationPort(IxePortRxObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'autoDetectInstrumentation'
    __tcl_members__ = [
        TclMember('enableMisdirectedPacketMask', type=bool),
        TclMember('enablePRBS', type=bool),
        TclMember('enableSignatureMask', type=bool),
        TclMember('misdirectedPacketMask'),
        TclMember('signature'),
        TclMember('signatureMask'),
        TclMember('startOfScan', type=int),
    ]


class IxeDataIntegrityPort(IxePortRxObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'dataIntegrity'
    __tcl_members__ = [
        TclMember('enableTimeStamp', type=bool),
        TclMember('insertSignature', type=bool),
        TclMember('floatingTimestampAndDataIntegrityMode'),
        TclMember('numBytesFromEndOfFrame', type=int),
        TclMember('payloadLength', type=int),
        TclMember('signature'),
        TclMember('signatureOffset', type=int),
    ]


class IxePacketGroupPort(IxePortRxObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'packetGroup'
    __tcl_members__ = [
        TclMember('allocateUdf', type=bool),
        TclMember('delayVariationMode'),
        TclMember('enable128kBinMode', type=bool),
        TclMember('enableGroupIdMask', type=bool),
        TclMember('enableInsertPgid', type=bool),
        TclMember('enableLastBitTimeStamp', type=bool),
        TclMember('enableLatencyBins', type=bool),
        TclMember('enableReArmFirstTimeStamp', type=bool),
        TclMember('enableRxFilter', type=bool),
        TclMember('enableSignatureMask', type=bool),
        TclMember('enableTimeBins', type=bool),
        TclMember('groupId', type=int),
        TclMember('groupIdMask'),
        TclMember('groupIdMode'),
        TclMember('groupIdOffset', type=int),
        TclMember('headerFilter'),
        TclMember('headerFilterMask'),
        TclMember('ignoreSignature', type=bool),
        TclMember('insertSequenceSignature', type=bool),
        TclMember('insertSignature', type=bool),
        TclMember('latencyBinList'),
        TclMember('latencyControl'),
        TclMember('maxRxGroupId', type=int),
        TclMember('measurementMode'),
        TclMember('multiSwitchedPathMode'),
        TclMember('numPgidPerTimeBin', type=int),
        TclMember('numTimeBins', type=int),
        TclMember('preambleSize', type=int),
        TclMember('seqAdvTrackingLateThreshold', type=int),
        TclMember('sequenceErrorThreshold', type=int),
        TclMember('sequenceCheckingMode'),
        TclMember('sequenceNumberOffset', type=int),
        TclMember('signature'),
        TclMember('signatureMask'),
        TclMember('signatureOffset', type=int),
        TclMember('timeBinDuration', type=int),
    ]
