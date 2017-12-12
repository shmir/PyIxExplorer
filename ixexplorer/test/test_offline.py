"""
IxExplorer package tests that can run in offline mode.

@author yoram@ignissoft.com
"""

from os import path

from ixexplorer.test.test_base import IxeTestBase
from trafficgenerator.tgn_utils import TgnError


class IxeTestOffline(IxeTestBase):

    def testLoadConfig(self):

        cfg1 = path.join(path.dirname(__file__), 'configs/test_config_1.prt')
        cfg2 = path.join(path.dirname(__file__), 'configs/test_config_2.prt')
        self._load_config(cfg1, cfg2)

        assert(len(self.ports) == 2)
        assert(len(self.ports[self.port1].streams) == 2)
        assert(len(self.ports[self.port2].streams) == 2)

        assert(self.ports[self.port1].streams[1].da == '22:22:22:22:22:11')
        assert(self.ports[self.port1].streams[1].sa == '11:11:11:11:11:11')
        assert(self.ports[self.port1].streams[2].da == '22:22:22:22:22:22')
        assert(self.ports[self.port1].streams[2].sa == '11:11:11:11:11:22')

        self.ports[self.port1].streams[1].da = '33:33:33:33:33:33'
        self.ports[self.port1].streams[1].sa = '44:44:44:44:44:44'
        self.ports[self.port1].streams[2].ip.ix_get(force=True)
        self.ports[self.port1].streams[2].ip.destIpAddr = '2.2.2.2'
        self.ports[self.port1].write()

        self.ixia.refresh()
        assert(self.ports[self.port1].streams[2].da == '22:22:22:22:22:22')
        assert(self.ports[self.port1].streams[2].sa == '11:11:11:11:11:22')
        assert(self.ports[self.port1].streams[1].da == '33:33:33:33:33:33')
        assert(self.ports[self.port1].streams[1].sa == '44:44:44:44:44:44')

    def testBuildConfig(self):
        self._reserve_ports()

        self.ports[self.port1].add_stream()
        self.ports[self.port1].streams[1].da = "22:22:22:22:22:11"
        self.ports[self.port1].streams[1].sa = "11:11:11:11:11:11"
        self.ports[self.port1].add_stream()
        self.ports[self.port1].streams[2].da = "22:22:22:22:22:22"
        self.ports[self.port1].streams[2].sa = "11:11:11:11:11:22"
        self.ports[self.port1].write()

        assert(self.ports[self.port1].streams[1].da == '22:22:22:22:22:11')
        assert(self.ports[self.port1].streams[1].sa == '11:11:11:11:11:11')
        assert(self.ports[self.port1].streams[2].da == '22:22:22:22:22:22')
        assert(self.ports[self.port1].streams[2].sa == '11:11:11:11:11:22')

        self.ports[self.port2].add_stream()
        self.ports[self.port2].streams[1].da = "11:11:11:11:11:11"
        self.ports[self.port2].streams[1].sa = "22:22:22:22:22:11"
        self.ports[self.port2].add_stream()
        self.ports[self.port2].streams[2].da = "11:11:11:11:11:22"
        self.ports[self.port2].streams[2].sa = "22:22:22:22:22:22"
        self.ports[self.port2].write()

        assert(self.ports[self.port1].streams[1].da == '22:22:22:22:22:11')
        assert(self.ports[self.port1].streams[1].sa == '11:11:11:11:11:11')
        assert(self.ports[self.port1].streams[2].da == '22:22:22:22:22:22')
        assert(self.ports[self.port1].streams[2].sa == '11:11:11:11:11:22')

    def testErrors(self):

        cfg = path.join(path.dirname(__file__), 'configs/good_to_bad_config.prt')
        port = self.ixia.session.reserve_ports([self.port1], force=True).values()[0]
        self.ixia.session.login('anotherUser')
        with self.assertRaises(TgnError):
            assert(port.reserve())
        self.ixia.session.login(self.config.get('IXE', 'user'))
        port.reserve()
        port.load_config(cfg)
        port.streams[1].framesize = 64
        with self.assertRaises(TgnError):
            assert(port.write())
