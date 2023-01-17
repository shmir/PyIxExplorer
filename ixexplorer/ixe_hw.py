
import re
from enum import Enum
from collections import OrderedDict

from trafficgenerator.tgn_tcl import tcl_list_2_py_list

from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY, IxTclHalError, ixe_obj_meta
from ixexplorer.ixe_object import IxeObject, IxeObjectObj
from ixexplorer.ixe_port import IxePort


class IxeCard(IxeObject, metaclass=ixe_obj_meta):
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

    regex = r'RG([\d]+)\s*mode\s*([\d]+)\s*ppm\s*([-]*[\d]*)\s*active ports\s\{([\s\d]*)\}\s*active capture ports\s\{([\s\d]*)\}\s*resource ports\s*\{([\s\d]*)\}'  # noqa

    def __init__(self, parent, uri):
        super().__init__(parent=parent, uri=uri.replace('/', ' '))

    def discover(self):
        self.logger.info('Discover card {}'.format(self.obj_name()))
        for pid in range(1, self.portCount + 1):
            IxePort(self, self.uri + '/' + str(pid))
        try:
            rg = self.resourceGroupInfoList
            if rg and rg != -1:
                rg_info_list = tcl_list_2_py_list(rg, within_tcl_str=True)
                for entry in rg_info_list:
                    matches = re.finditer(self.regex, entry.strip())
                    for match in matches:
                        IxeResourceGroup(self, str(int(match.group(1)) + 1), match.group(2), match.group(3),
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
        except Exception as _:
            print("no resource group support")

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

    def write(self):
        self.ix_command('write')
    #
    # Properties.
    #

    def get_ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """
        #return {int(p.index): p for p in self.get_objects_by_type('port')}
        return {p.index: p for p in self.get_objects_by_type('port')}
    ports = property(get_ports)

    def get_resource_groups(self):
        """
        :return: dictionary {resource group id: object} of all resource groups.
        """
        #resource_groups = {int(r.index): r for r in self.get_objects_by_type('resourceGroupEx')}
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


class IxeChassis(IxeObject, metaclass=ixe_obj_meta):
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
        super().__init__(parent=parent, uri=host, name=host)
        self.chassis_id = chassis_id

    def connect(self):
        self.add()
        self.id = self.chassis_id

    def disconnect(self):
        self.ix_command('del')

    def add_card(self, cid):
        # unfortunately there is no config option which cards are used. So
        # we have to iterate over all possible card ids and check if we are
        # able to get a handle.
        card = IxeCard(self, str(self.chassis_id) + '/' + str(cid))
        try:
            card.discover()
        except IxTclHalError:
            self.logger.info('slot {} is empty'.format(cid))
            card.del_object_from_parent()

    def discover(self):
        self.logger.info('Discover chassis {}'.format(self.obj_name()))
        for cid in range(1, self.maxCardCount + 1):
            self.add_card(cid)
            # unfortunately there is no config option which cards are used. So
            # we have to iterate over all possible card ids and check if we are
            # able to get a handle.
            # card = IxeCard(self, str(self.chassis_id) + '/' + str(cid))
            # try:
            #     card.discover()
            # except IxTclHalError:
            #     self.logger.info('slot {} is empty'.format(cid))
            #     card.del_object_from_parent()

    def add_vm_card(self, card_ip, card_id, keep_alive=300):
        self._api.call_rc('chassis addVirtualCard {} {} {} {}'.format(self.host, card_ip, card_id, keep_alive))
        return IxeCard(self._api, self, card_id)

    def remove_vm_card(self, card):
        self._api.call_rc('chassis removeVMCard {} {}'.format(self.host, card.id))

    def get_cards(self):
        """
        :return: dictionary {name: object} of all cards.
        """

        return {(c.index): c for c in self.get_objects_by_type('card')}
    cards = property(get_cards)

    def Refresh(self):
        self.refresh()
        self._reset_current_object()
#
# Card object classes.
#


class IxeCardObj(IxeObjectObj, metaclass=ixe_obj_meta):

    def __init__(self, parent, uri):
        super().__init__(parent=parent, uri=uri.replace('/', ' '))

    #
    # Properties.
    #

    def get_ports(self):
        """
        :return: dictionary {index: object} of all ports.
        """

        return {(p.index): p for p in self.get_objects_by_type('port')}
    ports = property(get_ports)


class splitSpeed(Enum):
    One_400G = '400000.1'
    Two_200G = '200000.2'
    One_200G = '200000.1'
    Four_100G = '100000.4'
    Two_100G = '100000.2'
    One_100G = '100000.1'
    Eight_50G = '50000.8'
    Four_50G = '50000.4'
    One_40G = '40000.1'
    Four_25G = '25000.4'
    Four_10G = '10000.4'
    Two_50G = '50000.2'

    def __eq__(self, other):
        return self.value == other.value

class IxeResourceGroup(IxeCardObj, metaclass=ixe_obj_meta):
    __tcl_command__ = 'resourceGroupEx'
    __tcl_members__ = [
        TclMember('mode', type=int),
        TclMember('activePortList'),
        TclMember('resourcePortList'),
        TclMember('activeCapturePortList'),
        TclMember('ppm')
    ]
    rePortInList = re.compile(r"(?:{((?:\d+\s*){3})})")

    def __init__(self, parent, rg_num, mode, ppm, active_ports, capture_ports, resource_ports):
        super().__init__(parent=parent, uri=parent.uri.replace('/', ' ') + ' ' + rg_num)
        self._update_uri(parent.uri.replace('/', ' ') + ' ' + str(active_ports[0]))
        self.active_ports = active_ports
        self.capture_ports = capture_ports
        self.resource_ports = resource_ports

    def enable_capture_state(self, state, writeToHw=False):
        """
        Enable/Disable capture on resource group
        """
        try :
            if state:
                activePorts = self.rePortInList.findall(self.activePortList)
                self.activeCapturePortList = "{{"+activePorts[0]+"}}"
            else:
                self.activeCapturePortList = "{{""}}"
            if (writeToHw):
                self.ix_command('write')
            return True
        except Exception as e:
            return False


    def change_mode(self, mode, writeToHw=False):
        new_mode = int(float(mode.value))
        if new_mode == self.mode:
            return None
        allPorts = self.rePortInList.findall(self.resourcePortList)
        self.set_auto_set(False)
        self.mode = new_mode
        self.set_auto_set(True)
        if mode in [splitSpeed.One_400G, splitSpeed.One_200G, splitSpeed.One_100G, splitSpeed.One_40G]:  #== 100000 or mode == 40000:
            self.activePortList = "{{" + allPorts[0] + "}}"
            activeIndex = 0
        elif mode in [splitSpeed.Four_100G,splitSpeed.Four_50G, splitSpeed.Four_25G, splitSpeed.Four_10G]:  #mode == 10000 or mode == 25000:
            self.activePortList = "{{" + allPorts[1] + "}{" + allPorts[2] + "}{" + allPorts[3] + "}{" + allPorts[4] + "}}"
            activeIndex = 1
        elif mode in [splitSpeed.Two_200G, splitSpeed.Two_100G, splitSpeed.Two_50G]:  #mode == 50000:
            self.activePortList = "{{" + allPorts[5] + "}{" + allPorts[6] + "}}"
            activeIndex = 5
        elif mode in [splitSpeed.Eight_50G]:  #mode == 50000:
            self.activePortList = "{{" + allPorts[7] + "}{" + allPorts[8] + "}{" + allPorts[9] + "}{" + allPorts[10] + "}{" + allPorts[11] + "}{" + allPorts[12] + "}{" + allPorts[13] + "}{" + allPorts[14] + "}}"
            activeIndex = 7
        else:
            return None
        if writeToHw:
            self.ix_command('write')
        self._update_uri(allPorts[activeIndex])
        return True

    def _update_uri(self, value):
        self._data['uri'] = value

