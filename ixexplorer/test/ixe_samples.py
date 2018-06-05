#!/usr/bin/env python

import logging
import sys

from ixexplorer.ixe_port import IxeLinkState
from ixexplorer.ixe_app import init_ixe

# IxTclServer address.
host = '192.168.42.61'
host = 'localhost'

# Windows - 4555, Linux - 8022
tcp_port = 8022
tcp_port = 4555

# Chassis IP address
ip = '192.168.42.175'
ip = '192.168.42.61'
ip = '192.168.28.7'
ip = 'localhost'
ip = '10.5.224.81'

user = 'pyixexplorer'

# Required only for Linux servers
rsa_id = '/opt/ixia/ixos-api/8.30.0.10/lib/ixTcl1.0/id_rsa'
rsa_id = 'C:/Program Files (x86)/Ixia/IxOS/8.40-EA/TclScripts/lib/ixTcl1.0/id_rsa'

vModule = '10.10.10.3'
mac = '00:00:00:00:00:00'

ixia = None


def link_state_str(link_state):
    if link_state in list(map(int, [e.value for e in IxeLinkState])):
        return IxeLinkState(link_state).name
    return str(link_state)


def connect():
    global ixia

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    ixia = init_ixe(logger, host, tcp_port, rsa_id)
    ixia.connect(user)



def disconnect():
    ixia.disconnect()


def discover():

    ixia.add(ip)
    ixia.discover()
    chassis = list(ixia.chassis_chain.values())[0]

    print ('%-7s | %-32s | %-10s' % ('Chassis', 'Type', 'Version'))
    print ('--------+----------------------------------+--------------')
    print ('%-7s | %-32s | %-10s' % (chassis.id, chassis.typeName, chassis.ixServerVersion))
    print (chassis.id)
    print ('')

    print ('%-4s | %-32s | %-10s | %s' % ('Card', 'Type', 'HW Version', 'Serial Number'))
    print ('-----+----------------------------------+------------+--------------')
    for card in chassis.cards.values():
        if card is not None:
            print('%-4s | %-32s | %-10s | %-s' % (card, card.typeName, card.hwVersion, card.serialNumber))

    print ('')
    print ('%-8s | %-8s | %-10s | %-s' % ('Port', 'Owner', 'Link State', 'Speeds'))
    print ('---------+----------+------------+-------------------------------')
    for card in chassis.cards.values():
        if card is None:
            continue
        for port in card.active_ports.values():
            port.wait_for_up()
            print ('%-8s | %-8s | %-10s | %-s' % (port, port.owner.strip(), link_state_str(port.linkState),
                                                  port.supported_speeds()))


def build_ixvm():

    card = ixia.chassis.add_vm_card(vModule, 2)
    card.add_vm_port(1, 'eth1', mac)
    card.add_vm_port(2, 'eth2', mac)




def test_split_modes():
    chassis = list(ixia.chassis_chain.values())[0]
    workingPort1 = "10.5.224.94/4/1"
    ixia.session.reserve_ports([workingPort1], clear=True, force=True)
    rg1 = chassis.cards[4].resource_groups[1]
    rg1.change_mode(100000)
    apl = rg1.activePortList
    rg1.change_mode(25000)
    apl = rg1.activePortList
    rg1.change_mode(50000)
    apl = rg1.activePortList
    rg1.change_mode(40000)
    apl = rg1.activePortList
    pass

if __name__ == '__main__':
    connect()
    discover()
    #test_split_modes()
    disconnect()
