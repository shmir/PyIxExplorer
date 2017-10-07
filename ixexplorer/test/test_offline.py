"""
Base class for all IxLoad package tests.

@author yoram@ignissoft.com
"""

from os import path

from ixexplorer.test.test_base import IxeTestBase


class IxExplorerTestBase(IxeTestBase):

    def testLoadConfig(self):
        ports = self.ixia.session.reserve_ports(self.port1, self.port2)
        cfg1 = path.join(path.dirname(__file__), 'c:/configs/test_config_1.str').replace('\\', '/')
        ports[self.port1].load_config(cfg1)
        cfg2 = path.join(path.dirname(__file__), 'c:/configs/test_config_2.str').replace('\\', '/')
        ports[self.port2].load_config(cfg2)
