#!/usr/bin/env python

import logging
import sys

from trafficgenerator.tgn_utils import ApiType
from ixexplorer.ixe_port import IxePort
from ixexplorer.ixe_app import init_ixe

# API type = tcl or socket, currently supports only socket.
api = ApiType.socket

# IxTclServer address.
host = '192.168.42.61'

# Windows - 4555, Linux - 8022
tcp_port = 4555

# Chassis IP address
ip = '192.168.28.7'
ip = '192.168.42.175'
ip = '192.168.42.61'

user = 'pyixexplorer'

# Required only for Linux servers
rsa_id = '/opt/ixia/ixos-api/8.30.0.10/lib/ixTcl1.0/id_rsa'
rsa_id = 'C:/Program Files (x86)/Ixia/IxOS/8.30-EA/TclScripts/lib/ixTcl1.0/id_rsa'

vModule = '10.10.10.3'
mac = '00:00:00:00:00:00'

ixia = None


def link_state_str(link_state):
    prefix = 'LINK_STATE_'
    for attr in dir(IxePort):
        if attr.startswith(prefix):
            val = getattr(IxePort, attr)
            if val == link_state:
                return attr[len(prefix):]
    return link_state


def connect():
    global ixia

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    ixia = init_ixe(api, logger, host, tcp_port, rsa_id)
    ixia.connect(user)


def disconnect():
    ixia.disconnect()


def discover():
    connect()

    ixia.add(ip)
    ixia.discover()
    chassis = ixia.chassis_chain.values()[0]

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
        for port in card.ports.values():
            print ('%-8s | %-8s | %-10s | %-s' % (port, port.owner.strip(), link_state_str(port.linkState),
                                                  port.supported_speeds()))

    disconnect()


def start_transmit():
    connect()
    ixia.add(ip)
    ixia.session.reserve_ports([ip + '/1/1', ip + '/1/2'])


def build_ixvm():

    connect()

    card = ixia.chassis.add_vm_card(vModule, 2)
    card.add_vm_port(1, 'eth1', mac)
    card.add_vm_port(2, 'eth2', mac)

    disconnect()


def detailed_log():

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
    ixia = init_ixe(api, logging.getLogger(), host, tcp_port, rsa_id)
    ixia.connect(ip)
    ixia.disconnect()


if __name__ == '__main__':
    start_transmit()
