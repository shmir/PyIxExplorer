"""
Base class for all IxLoad package tests.

@author yoram@ignissoft.com
"""

from os import path
import time

from trafficgenerator.tgn_utils import ApiType
from trafficgenerator.test.test_tgn import TgnTest

from ixexplorer.ixe_app import init_ixe
from ixexplorer.ixe_hw import PortGroup


class IxExplorerTestBase(TgnTest):

    TgnTest.config_file = path.join(path.dirname(__file__), 'IxExplorer.ini')

    def setUp(self):
        super(IxExplorerTestBase, self).setUp()
        self.ixia = init_ixe(ApiType[self.config.get('IXE', 'api')], self.logger,
                             host=self.config.get('IXE', 'server'))
        self.ixia.connect()
        self.ixia.session.login('pyixexplorer')
        self.ixia.discover()

    def tearDown(self):
        super(IxExplorerTestBase, self).tearDown()

    def testHelloWorld(self):
        pass

    def testAll(self):
        self.ixia.chassis.get_ports()['1/1/1'].reserve()
        self.ixia.chassis.get_ports()['1/1/2'].reserve()
        self.ixia.chassis.get_ports()['1/1/1'].set_factory_defaults()
        self.ixia.chassis.get_ports()['1/1/2'].set_factory_defaults()
        cfg1 = path.join(path.dirname(__file__), 'c:/configs/test_config_1.str').replace('\\', '/')
        self.ixia.chassis.get_ports()['1/1/1'].load_config(cfg1)
        cfg2 = path.join(path.dirname(__file__), 'c:/configs/test_config_2.str').replace('\\', '/')
        self.ixia.chassis.get_ports()['1/1/2'].load_config(cfg2)

        pg = PortGroup()
        pg.create()
        pg.add_port(self.ixia.chassis.get_ports()['1/1/1'])
        pg.add_port(self.ixia.chassis.get_ports()['1/1/2'])

        pg.start_transmit()
        time.sleep(8)
        pg.stop_transmit()
        time.sleep(2)

        print('1/1/1 bytesReceived = ' + str(self.ixia.chassis.get_ports()['1/1/1'].stats.bytes_received))
        print('1/1/1 bytesSent = ' + str(self.ixia.chassis.get_ports()['1/1/1'].stats.bytes_sent))
        print('1/1/2 bytesReceived = ' + str(self.ixia.chassis.get_ports()['1/1/2'].stats.bytes_received))
        print('1/1/2 bytesSent = ' + str(self.ixia.chassis.get_ports()['1/1/2'].stats.bytes_sent))

        pg.destroy()

    #
    # Auxiliary functions, no testing inside.
    #

    def _reserve_ports(self):
        self.pg = PortGroup(self._api, id)
