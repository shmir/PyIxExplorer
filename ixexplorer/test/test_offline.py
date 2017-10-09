"""
IxExplorer package tests that can run in offline mode.

@author yoram@ignissoft.com
"""

from ixexplorer.test.test_base import IxeTestBase


class IxExplorerTestBase(IxeTestBase):

    def testLoadConfig(self):
        cfg1 = 'c:/configs/test_config_1.str'
        cfg2 = 'c:/configs/test_config_2.str'
        self._load_config(cfg1, cfg2)

    def testBuildConfig(self):
        self._reserve_ports()
        stream = self.ports[self.port1].add_stream()
        stream.da = "11:11:11:11:11:11"
        stream.sa = "11:11:11:11:11:11"
        stream = self.ports[self.port1].add_stream()
        stream.da = "22:22:22:22:22:22"
        stream.sa = "22:22:22:22:22:22"
        self.ports[self.port1].write()
