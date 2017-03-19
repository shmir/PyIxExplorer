"""
Base class for all IxLoad package tests.

@author yoram@ignissoft.com
"""

from os import path

from trafficgenerator.test.test_tgn import TgnTest

from ixexplorer.ixe_app import Ixia, PortGroup


class IxExplorerTestBase(TgnTest):

    TgnTest.config_file = path.join(path.dirname(__file__), 'IxExplorer.ini')

    def setUp(self):
        super(IxExplorerTestBase, self).setUp()
        ixia = Ixia(self.config.get('IXE', 'chassis'), int(self.config.get('IXE', 'tcp_port')))
        ixia.connect()
        ixia.session.login('pyixia')
        ixia.discover()

    def tearDown(self):
        super(IxExplorerTestBase, self).tearDown()

    def testHelloWorld(self):
        pass

    #
    # Auxiliary functions, no testing inside.
    #

    def _reserve_ports(self):
        self.pg = PortGroup(self._api, id)
