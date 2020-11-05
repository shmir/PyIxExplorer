#!/usr/bin/env python
# encoding: utf-8

import json
import logging
import sys
import time
from typing import Optional

from ixexplorer.ixe_port import IxeLinkState
from ixexplorer.ixe_app import init_ixe, IxeApp

log_level = logging.DEBUG


chassis_ip = '192.168.65.30'
host_port = f'{chassis_ip}:8022'
port1 = f'{chassis_ip}/1/1'
port2 = f'{chassis_ip}/1/2'

user = 'pyixexplorer'

# Required only for Linux servers
rsa_id = 'C:/Program Files (x86)/Ixia/IxOS/9.00.1900.10/TclScripts/lib/ixTcl1.0/id_rsa'


ixia: Optional[IxeApp] = None


def link_state_str(link_state):
    if link_state in list(map(int, [e.value for e in IxeLinkState])):
        return IxeLinkState(link_state).name
    return str(link_state)


def connect():
    global ixia

    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.addHandler(logging.StreamHandler(sys.stdout))

    host, port = host_port.split(':')

    ixia = init_ixe(logger, host, int(port), rsa_id)
    ixia.connect(user)
    ixia.add(chassis_ip)


def disconnect():
    ixia.disconnect()


def discover():

    ixia.discover()
    chassis = list(ixia.chassis_chain.values())[0]

    print('%-7s | %-32s | %-10s' % ('Chassis', 'Type', 'Version'))
    print('--------+----------------------------------+--------------')
    print('%-7s | %-32s | %-10s' % (chassis.id, chassis.typeName, chassis.ixServerVersion))
    print(chassis.id)
    print('')

    print('%-4s | %-32s | %-10s | %s' % ('Card', 'Type', 'HW Version', 'Serial Number'))
    print('-----+----------------------------------+------------+--------------')
    for card in chassis.cards.values():
        if card is not None:
            print('%-4s | %-32s | %-10s | %-s' % (card, card.typeName, card.hwVersion, card.serialNumber))

    print('')
    print('%-8s | %-8s | %-10s | %-s' % ('Port', 'Owner', 'Link State', 'Speeds'))
    print('---------+----------+------------+-------------------------------')
    for card in chassis.cards.values():
        if card is None:
            continue
        for port in card.active_ports.values():
            print('%-8s | %-8s | %-10s | %-s' % (port, port.owner.strip(), link_state_str(port.linkState),
                                                 port.supported_speeds()))


def build_and_run():

    ports = ixia.session.reserve_ports([port1, port2], force=True)
    stream11 = ports[port1].add_stream()
    stream11.rateMode = 'streamRateModePercentRate'
    stream11.percentPacketRate = 95
    stream12 = ports[port2].add_stream()
    stream12.rateMode = 'streamRateModePercentRate'
    stream12.percentPacketRate = 95

    ports[port1].write()
    ports[port2].write()

    ports[port1].clear_all_stats()
    ports[port2].clear_all_stats()
    ixia.session.start_transmit()
    time.sleep(8)
    ixia.session.stop_transmit()
    time.sleep(2)
    port1_stats = ports[port1].read_stats()
    port2_stats = ports[port2].read_stats()

    print(json.dumps(port1_stats, indent=2))
    print(json.dumps(port1_stats, indent=2))

    assert(port1_stats['framesSent'], port2_stats['framesReceived'])


if __name__ == '__main__':
    connect()
    discover()
    build_and_run()
    disconnect()
