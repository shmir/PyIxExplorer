"""
Base class for all IxLoad package tests.

@author yoram@ignissoft.com
"""

from ixexplorer.test.test_base import IxeTestBase


class IxExplorerTestBase(IxeTestBase):

    def testLoadConfig(self):
        self.ixia.session.reserve_ports(self.config.get('IXE', 'port1'), self.config.get('IXE', 'port2'))
