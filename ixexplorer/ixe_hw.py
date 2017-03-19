
from pyixia.ixapi import _MetaIxTclApi, TclMember, FLAG_RDONLY
from pyixia.ixapi import IxTclHalError

from ixexplorer.ixe_object import IxeObject, Statistics


class Port(IxeObject):
    __metaclass__ = _MetaIxTclApi
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

    def __init__(self, tcl, parent, id):
        self.card = parent
        self.id = id
        self._api = tcl
        self.stats = Statistics(tcl, self)

    def _ix_get(self, member):
        self._api.call_rc('port get %d %d %d', *self._port_id())

    def _ix_set(self, member):
        self._api.call_rc('port set %d %d %d', *self._port_id())

    def _port_id(self):
        return self.card._card_id() + (self.id,)

    def __str__(self):
        return '%d/%d/%d' % self._port_id()


class Card(IxeObject):
    __metaclass__ = _MetaIxTclApi
    __tcl_command__ = 'card'
    __tcl_members__ = [
            TclMember('cardOperationMode', type=int, flags=FLAG_RDONLY),
            TclMember('clockRxRisingEdge', type=int),
            TclMember('clockSelect', type=int),
            TclMember('clockTxRisingEdge', type=int),
            TclMember('fpgaVersion', type=int, flags=FLAG_RDONLY),
            TclMember('hwVersion', type=int, flags=FLAG_RDONLY),
            TclMember('portCount', type=int, flags=FLAG_RDONLY),
            TclMember('serialNumber', type=int, flags=FLAG_RDONLY),
            TclMember('txFrequencyDeviation', type=int),
            TclMember('type', type=int, flags=FLAG_RDONLY),
            TclMember('typeName'),
    ]

    TYPE_NONE = 0

    def __init__(self, api, parent, id):
        self.chassis = parent
        self.id = id
        self.ports = []
        self._api = api

    def _ix_get(self, member):
        self._api.call_rc('card get %d %d', *self._card_id())

    def _ix_set(self, member):
        self._api.call_rc('card set %d %d', *self._card_id())

    def discover(self):
        for pid in xrange(self.port_count):
            pid += 1
            port = Port(self._api, self, pid)
            self.logger.info('Adding port %s', port)
            self.ports.append(port)

    def _card_id(self):
        return (self.chassis.id, self.id)

    def __str__(self):
        return '%d/%d' % self._card_id()

    def add_vm_port(self, port_id, nic_id, mac, promiscuous=0, mtu=1500, speed=1000):
        card_id = self._card_id()
        self._api.call_rc('card addVMPort {} {} {} {} {} {} {} {}'.
                          format(card_id[0], card_id[1], port_id, nic_id, promiscuous, mac, mtu, speed))
        return Port(self._api, self, port_id)

    def remove_vm_port(self, card):
        self._api.call_rc('chassis removeVMCard {} {}'.format(self.host, card.id))


class Chassis(IxeObject):
    __metaclass__ = _MetaIxTclApi
    __tcl_command__ = 'chassis'
    __tcl_members__ = [
            TclMember('baseIpAddress'),
            TclMember('cableLength', type=int),
            TclMember('hostname', flags=FLAG_RDONLY),
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

    def __init__(self, host):
        self.host = host
        self.cards = []

    def _ix_add(self):
        self._api.call_rc('chassis add %s', self.host)

    def _ix_del(self):
        self._api.call_rc('chassis del %s', self.host)

    def _ix_get(self, member):
        self._api.call_rc('chassis get %s', self.host)

    def _ix_set(self, member):
        self._api.call_rc('chassis set %s', self.host)

    def connect(self, chassis_id=1):
        self._ix_add()
        self.id = chassis_id

    def disconnect(self):
        self._ix_del()

    def discover(self):
        self.logger.info('Discover chassis %d (%s)', self.id, self.type_name)
        for cid in xrange(self.max_card_count):
            # unfortunately there is no config option which cards are used. So
            # we have to iterate over all possible card ids and check if we are
            # able to get a handle.
            cid += 1
            try:
                card = Card(self._api, self, cid)
                self.logger.info('Adding card %s (%s)', card, card.type_name)
                card.discover()
                self.cards.append(card)
            except IxTclHalError:
                # keep in sync with card ids
                self.cards.append(None)

    def add_vm_card(self, card_ip, card_id, keep_alive=300):
        self._api.call_rc('chassis addVirtualCard {} {} {} {}'.format(self.host, card_ip, card_id, keep_alive))
        return Card(self._api, self, card_id)

    def remove_vm_card(self, card):
        self._api.call_rc('chassis removeVMCard {} {}'.format(self.host, card.id))
