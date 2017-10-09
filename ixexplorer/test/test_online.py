"""
TestCenter package tests that require actual Ixia chassis and active ports.

Test setup:
Two Ixia ports connected back to back.

@author yoram@ignissoft.com
"""

import time

from ixexplorer.ixe_hw import IxePortGroup
from ixexplorer.test.test_base import IxeTestBase


class IxExplorerTestBase(IxeTestBase):

    def testAll(self):
        cfg1 = 'c:/configs/test_config_1.prt'
        cfg2 = 'c:/configs/test_config_2.prt'
        self._load_config(cfg1, cfg2)

        pg = IxePortGroup()
        pg.create()
        pg.add_port(self.ports[self.port1])
        pg.add_port(self.ports[self.port2])

        pg.start_transmit()
        time.sleep(8)
        pg.stop_transmit()
        time.sleep(2)

        print('{} bytesReceived = {}'.format(self.port1, self.ports[self.port1].stats.bytes_received))
        print('{} bytesSent = {}'.format(self.port1, self.ports[self.port1].stats.bytes_sent))
        print('{} bytesReceived = {}'.format(self.port2, self.ports[self.port2].stats.bytes_received))
        print('{} bytesSent = {}'.format(self.port2, self.ports[self.port2].stats.bytes_sent))

        print('{} bytesReceived = {}'.format(self.port1, self.ports[self.port1].stats.bits_received))
        print('{} bytesSent = {}'.format(self.port1, self.ports[self.port1].stats.bits_sent))
        print('{} bytesReceived = {}'.format(self.port2, self.ports[self.port2].stats.bits_received))
        print('{} bytesSent = {}'.format(self.port2, self.ports[self.port2].stats.bits_sent))

        pg.destroy()
