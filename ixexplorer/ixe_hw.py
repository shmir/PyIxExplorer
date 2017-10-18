
from os import path
import re

from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY, IxTclHalError
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_stream import IxeStream


class IxePort(IxeObject):
    __tcl_command__ = 'port'
    __tcl_members__ = [
            TclMember('name'),
            TclMember('owner', flags=FLAG_RDONLY),
            TclMember('type', type=int, flags=FLAG_RDONLY),
            TclMember('loopback'),
            TclMember('flowControl'),
            TclMember('linkState', type=int, flags=FLAG_RDONLY),
            TclMember('portMode', type=int),
            TclMember('transmitMode'),
    ]

    __tcl_commands__ = ['export', 'getFeature', 'getStreamCount', 'reset', 'setFactoryDefaults', 'write']

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

    def supported_speeds(self):
        return re.findall(r'\d+', self.getFeature('ethernetLineRate'))

    def reserve(self, force=False):
        """ Reserve port.

        :param force: True - take forcefully, False - fail if port is reserved by other user
        """

        if not force:
            self.api.call_rc('ixPortTakeOwnership {}'.format(self.uri))
        else:
            self.api.call_rc('ixPortTakeOwnership {} force'.format(self.uri))

    def release(self):
        self.api.call_rc('ixPortClearOwnership {}'.format(self.uri))

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

    def stop_capture(self, cap_file_name):
        """ Stop capture on port.

        :param cap_file_name: prefix for the capture file name.
            Capture file will be saved as pcap file named 'prefix' + 'URI'.pcap.
        :return: full path to pcap file if capture exists else None
        """

        full_cap_file_name = self.session.stop_capture(cap_file_name, self)
        return full_cap_file_name.get(self, None)


class IxeCard(IxeObject):
    __tcl_command__ = 'card'
    __tcl_members__ = [
            TclMember('cardOperationMode', type=int, flags=FLAG_RDONLY),
            TclMember('clockRxRisingEdge', type=int),
            TclMember('clockSelect', type=int),
            TclMember('clockTxRisingEdge', type=int),
            TclMember('fpgaVersion', type=int, flags=FLAG_RDONLY),
            TclMember('hwVersion', type=int, flags=FLAG_RDONLY),
            TclMember('portCount', type=int, flags=FLAG_RDONLY),
            TclMember('serialNumber', flags=FLAG_RDONLY),
            TclMember('txFrequencyDeviation', type=int),
            TclMember('type', type=int, flags=FLAG_RDONLY),
            TclMember('typeName'),
    ]

    TYPE_NONE = 0

    def __init__(self, parent, uri):
        super(self.__class__, self).__init__(uri=uri.replace('/', ' '), parent=parent)

    def discover(self):
        self.logger.info('Discover card {}'.format(self.obj_name()))
        for pid in range(1, self.portCount + 1):
            IxePort(self, self.uri + '/' + str(pid))

    def add_vm_port(self, port_id, nic_id, mac, promiscuous=0, mtu=1500, speed=1000):
        card_id = self._card_id()
        self._api.call_rc('card addVMPort {} {} {} {} {} {} {} {}'.
                          format(card_id[0], card_id[1], port_id, nic_id, promiscuous, mac, mtu, speed))
        return IxePort(self._api, self, port_id)

    def remove_vm_port(self, card):
        self._api.call_rc('chassis removeVMCard {} {}'.format(self.host, card.id))

    def get_ports(self):
        """
        :return: dictionary {name: object} of all ports.
        """

        return {int(p.uri[-1]): p for p in self.get_objects_by_type('port')}
    ports = property(get_ports)


class IxeChassis(IxeObject):
    __tcl_command__ = 'chassis'
    __tcl_members__ = [
            TclMember('baseIpAddress'),
            TclMember('cableLength', type=int),
            TclMember('hostName', flags=FLAG_RDONLY),
            TclMember('id', type=int),
            TclMember('ipAddress', flags=FLAG_RDONLY),
            TclMember('ixServerVersion', flags=FLAG_RDONLY),
            TclMember('master', flags=FLAG_RDONLY),
            TclMember('maxCardCount', type=int, flags=FLAG_RDONLY),
            TclMember('name'),
            TclMember('operatingSystem', type=int, flags=FLAG_RDONLY),
            TclMember('sequence', type=int),
            TclMember('type', type=int, flags=FLAG_RDONLY),
            TclMember('typeName', flags=FLAG_RDONLY),
    ]

    __tcl_commands__ = ['add']

    TYPE_1600 = 2
    TYPE_200 = 3
    TYPE_400 = 4
    TYPE_100 = 5
    TYPE_400C = 6
    TYPE_1600T = 7
    TYPE_DEMO = 9
    TYPE_OPTIXIA = 10
    TYPE_OPIXJR = 11
    TYPE_400T = 14
    TYPE_250 = 17
    TYPE_400TF = 18
    TYPE_OPTIXIAX16 = 19
    TYPE_OPTIXIAXL10 = 20
    TYPE_OPTIXIAXM12 = 22
    TYPE_OPTIXIAXV = 24

    TYPES = {2: 'ixia1600', 'ixia1600': 2,
             3: 'ixia200', 'ixia200': 3,
             4: 'ixia400', 'ixia400': 4,
             5: 'ixia100', 'ixia100': 5,
             6: 'ixia400C', 'ixia400C': 6,
             7: 'ixia1600T', 'ixia1600T': 7,
             9: 'ixiaDemo', 'ixiaDemo': 9,
             10: 'ixiaOptixia', 'ixiaOptixia': 10,
             11: 'ixiaOpixJr', 'ixiaOpixJr': 11,
             14: 'ixia400T', 'ixia400T': 14,
             17: 'ixia250', 'ixia250': 17,
             18: 'ixia400Tf', 'ixia400Tf': 18,
             19: 'ixiaOptixiaX16', 'ixiaOptixiaX16': 19,
             20: 'ixiaOptixiaXL10', 'ixiaOptixiaXL10': 20,
             22: 'ixiaOptixiaXM12', 'ixiaOptixiaXM12': 22,
             24: 'ixiaOptixiaXV', 'ixiaOptixiaXV': 24}

    OS_UNKNOWN = 0
    OS_WIN95 = 1
    OS_WINNT = 2
    OS_WIN2000 = 3
    OS_WINXP = 4

    def __init__(self, host, chassis_id=1):
        super(self.__class__, self).__init__(uri=host, parent=IxeObject.session, name=host)
        self.chassis_id = chassis_id

    def connect(self):
        self.add()
        self.id = self.chassis_id

    def disconnect(self):
        self.ix_command('del')

    def discover(self):
        self.logger.info('Discover chassis {}'.format(self.obj_name()))
        for cid in range(1, self.maxCardCount + 1):
            # unfortunately there is no config option which cards are used. So
            # we have to iterate over all possible card ids and check if we are
            # able to get a handle.
            card = IxeCard(self, str(self.chassis_id) + '/' + str(cid))
            try:
                card.discover()
            except IxTclHalError:
                card.del_object_from_parent()

    def add_vm_card(self, card_ip, card_id, keep_alive=300):
        self._api.call_rc('chassis addVirtualCard {} {} {} {}'.format(self.host, card_ip, card_id, keep_alive))
        return IxeCard(self._api, self, card_id)

    def remove_vm_card(self, card):
        self._api.call_rc('chassis removeVMCard {} {}'.format(self.host, card.id))

    def get_cards(self):
        """
        :return: dictionary {name: object} of all cards.
        """

        return {int(c.uri[-1]): c for c in self.get_objects_by_type('card')}
    cards = property(get_cards)
