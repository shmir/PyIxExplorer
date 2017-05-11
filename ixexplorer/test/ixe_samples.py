#!/usr/bin/env python

import logging
import sys

from ixexplorer.pyixia import Port
from ixexplorer.ixe_app import IxeApp

host = '192.168.42.174'
# For Linux servers use 8022
tcp_port = 8022
# Required only for Linux servers
rsa_id = 'C:/Program Files (x86)/Ixia/IxOS/8.20-EA/TclScripts/lib/ixTcl1.0/id_rsa'

vModule = '10.10.10.3'
mac = '00:00:00:00:00:00'

ixia = None


def link_state_str(link_state):
    prefix = 'LINK_STATE_'
    for attr in dir(Port):
        if attr.startswith(prefix):
            val = getattr(Port, attr)
            if val == link_state:
                return attr[len(prefix):]
    return link_state


def connect():
    global ixia

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    logging.getLogger().addHandler(logging.FileHandler('c:/temp/ixeooapi.log'))
    logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))

    ixia = IxeApp(logging.getLogger(), host, tcp_port, rsa_id)
    ixia.connect()


def disconnect():
    ixia.disconnect()


def discover():
    connect()

    ixia.discover()

    print ixia.chassis.type_name
    print ''

    print '%-4s | %-32s | %-10s | %s' % ('Card', 'Type', 'HW Version', 'Serial Number')
    print '-----+----------------------------------+------------+--------------'
    for card in ixia.chassis.cards:
        if card is not None:
            print '%-4s | %-32s | %-10s | %-s' % (card, card.type_name, card.hw_version, card.serial_number)

    print ''
    print '%-8s | %-8s | %-10s | %-s' % ('Port', 'Owner', 'Link State', 'Speeds')
    print '---------+----------+------------+-------------------------------'
    for card in ixia.chassis.cards:
        if card is None:
            continue
        for port in card.ports:
            print '%-8s | %-8s | %-10s | %-s' % (port, port.owner.strip(), link_state_str(port.link_state),
                                                 port.supported_speeds())

    disconnect()


def build_ixvm():

    connect()

    card = ixia.chassis.add_vm_card(vModule, 2)
    card.add_vm_port(1, 'eth1', mac)
    card.add_vm_port(2, 'eth2', mac)

    disconnect()


def take_ownership():

    connect()

    ixia.discover()
    ixia.session.login('ixe_samples')
    pg = ixia.new_port_group()
    pg.create()
    pg.add_port(ixia.chassis.cards[0].ports[0])
    pg.add_port(ixia.chassis.cards[0].ports[1])
    pg.take_ownership()
    pg.destroy()

    disconnect()


if __name__ == '__main__':
    take_ownership()
