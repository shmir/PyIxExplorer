
import re
from collections import OrderedDict

from trafficgenerator.tgn_tcl import tcl_list_2_py_list

from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY, IxTclHalError
from ixexplorer.ixe_object import IxeObject, IxeObjectObj
from ixexplorer.ixe_port import IxePort


class IxeCard(IxeObject):
    __tcl_command__ = 'card'
    __tcl_members__ = [
            TclMember('operationMode', type=int, flags=FLAG_RDONLY),
            TclMember('clockRxRisingEdge', type=int),
            TclMember('clockSelect', type=int),
            TclMember('clockTxRisingEdge', type=int),
            TclMember('fpgaVersion', type=int, flags=FLAG_RDONLY),
            TclMember('hwVersion', type=int, flags=FLAG_RDONLY),
            TclMember('portCount', type=int, flags=FLAG_RDONLY),
            TclMember('resourceGroupInfoList', flags=FLAG_RDONLY),
            TclMember('serialNumber', flags=FLAG_RDONLY),
            TclMember('txFrequencyDeviation', type=int),
            TclMember('type', type=int, flags=FLAG_RDONLY),
            TclMember('typeName', flags=FLAG_RDONLY),
    ]

    TYPE_NONE = 0

    regex = r'RG([\d]+)\s*mode\s*([\d]+)\s*ppm\s*([-]*[\d]+)\s*active ports\s\{([\s\d]*)\}\s*active capture ports\s\{([\s\d]*)\}\s*resource ports\s*\{([\s\d]*)\}'  # noqa

    def __init__(self, parent, uri):
        super(self.__class__, self).__init__(uri=uri.replace('/', ' '), parent=parent)

    def discover(self):
        self.logger.info('Discover card {}'.format(self.obj_name()))
        for pid in range(1, self.portCount + 1):
            IxePort(self, self.uri + '/' + str(pid))
        rg_info_list = tcl_list_2_py_list(self.resourceGroupInfoList, within_tcl_str=True)
        for entry in rg_info_list:
            matches = re.finditer(self.regex, entry.strip())
            for match in matches:
                IxeResourceGroup(self, match.group(1), match.group(2), match.group(3),
                                 [int(p) for p in match.group(4).strip().split()],
                                 [int(p) for p in match.group(5).strip().split()],
                                 [int(p) for p in match.group(6).strip().split()])
        if self.type == 110:
            operationMode = self.operationMode
            if operationMode == 2:
                ports = [13]
                operationMode = '10000'
            else:
                ports = range(1, 13)
                operationMode = '1000'
            IxeResourceGroup(self, 1, operationMode, -1, ports, ports, ports)

    def add_vm_port(self, port_id, nic_id, mac, promiscuous=0, mtu=1500, speed=1000):
        card_id = self._card_id()
        self._api.call_rc('card addVMPort {} {} {} {} {} {} {} {}'.
                          format(card_id[0], card_id[1], port_id, nic_id, promiscuous, mac, mtu, speed))
        return IxePort(self._api, self, port_id)

    def remove_vm_port(self, card):
        self._api.call_rc('chassis removeVMCard {} {}'.format(self.host, card.id))

    #
    # Card objects.
    #

    def get_resource_group(self):
        return self._get_object('_resourceGroup', IxeResourceGroup)
    resourceGroup = property(get_resource_group)

    #
    # Properties.
    #

    def get_ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """

        return {p.index: p for p in self.get_objects_by_type('port')}
    ports = property(get_ports)

    def get_resource_groups(self):
        """
        :return: dictionary {resource group id: object} of all resource groups.
        """

        resource_groups = {r.index: r for r in self.get_objects_by_type('resourceGroupEx')}
        return OrderedDict(sorted(resource_groups.items()))
    resource_groups = property(get_resource_groups)

    def get_active_ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """

        if not self.resource_groups:
            return self.ports
        else:
            active_ports = OrderedDict()
            for resource_group in self.resource_groups.values():
                for active_port in resource_group.active_ports:
                    active_ports[active_port] = self.ports[active_port]
            return active_ports
    active_ports = property(get_active_ports)


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

    __tcl_commands__ = ['add', 'del', 'refresh']

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

    def __init__(self, parent, host, chassis_id=1):
        super(self.__class__, self).__init__(uri=host, parent=parent, name=host)
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
                self.logger.info('slot {} is empty'.format(cid))
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

        return {c.index: c for c in self.get_objects_by_type('card')}
    cards = property(get_cards)

#
# Card object classes.
#


class IxeCardObj(IxeObjectObj):

    def __init__(self, parent, uri):
        super(IxeCardObj, self).__init__(uri=uri.replace('/', ' '), parent=parent)

    #
    # Properties.
    #

    def get_ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """

        return {p.index: p for p in self.get_objects_by_type('port')}
    ports = property(get_ports)


class IxeResourceGroup(IxeCardObj):
    __tcl_command__ = 'resourceGroupEx'
    __tcl_members__ = [
    ]

    def __init__(self, parent, rg_num, mode, ppm, active_ports, capture_ports, resource_ports):
        super(IxeCardObj, self).__init__(uri=parent.uri.replace('/', ' ') + ' ' + str(rg_num), parent=parent)
        self.mode = mode
        self.ppm = ppm
        self.active_ports = active_ports
        self.capture_ports = capture_ports
        self.resource_ports = resource_ports
