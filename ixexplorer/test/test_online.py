"""
TestCenter package tests that require actual Ixia chassis and active ports.

Test setup:
Two Ixia ports connected back to back.

@author yoram@ignissoft.com
"""

from os import path
import time

from ixexplorer.ixe_statistics_view import IxePortsStats, IxeStreamsStats, IxeCapFileFormat
from ixexplorer.test.test_base import IxeTestBase


class IxeTestOnline(IxeTestBase):

    def testPortStats(self):
        cfg1 = path.join(path.dirname(__file__), 'configs/stats_config_1.prt')
        cfg2 = path.join(path.dirname(__file__), 'configs/stats_config_2.prt')
        self._load_config(cfg1, cfg2)

        self.ixia.session.start_transmit()
        port_stats = IxePortsStats(self.ixia.session)
        port_stats.read_stats()
        print('++++')
        for port, stats in port_stats.statistics.items():
            print('{}\n\t{}'.format(port, stats))
        print('++++')
        self.ixia.session.stop_transmit()

        self.ports[self.port1].start_transmit()
        print('++++')
        print('{}\n\t{}'.format(self.ports[self.port1],
                                self.ports[self.port1].read_stats('framesSent', 'framesReceived')))
        print('++++')
        self.ports[self.port1].stop_transmit()

    def testCapture(self):
        cfg1 = path.join(path.dirname(__file__), 'configs/cap_config.prt')
        cfg2 = path.join(path.dirname(__file__), 'configs/cap_config.prt')
        self._load_config(cfg1, cfg2)

        for port in self.ports.values():
            port.start_capture()
            port.start_transmit()
        time.sleep(4)
        for name, port in self.ports.items():
            port.stop_transmit()
            port.stop_capture(cap_file_name=None, cap_file_format=IxeCapFileFormat.mem)
            print(name)
            print(port.get_cap_frames(1, 3, 5))

        self.ixia.session.start_capture()
        self.ixia.session.start_transmit()
        time.sleep(4)
        self.ixia.session.stop_transmit()
        self.ixia.session.stop_capture(cap_file_name='c:/temp/ixia__session_cap', cap_file_format=IxeCapFileFormat.txt)
        for name, port in self.ports.items():
            print(name)
            print(port.cap_file_name)
            print(port.get_cap_file())

    def testStreamStats(self):
        cfg1 = path.join(path.dirname(__file__), 'configs/stats_config_1.prt')
        cfg2 = path.join(path.dirname(__file__), 'configs/stats_config_2.prt')
        self._load_config(cfg1, cfg2)

        self.ixia.session.start_transmit()

        stream_stats = IxeStreamsStats(self.ixia.session)
        time.sleep(2)
        self.ixia.session.stop_transmit()

        stream_stats.read_stats()
        print('++++')
        for stream, stats in stream_stats.statistics.items():
            print('{}\n\t{}\n\t{}'.format(stream, stats['tx'], {str(p): s for p, s in stats['rx'].items()}))
        print('++++')

        print('++++')
        print('{}\n\t{}'.format(self.ports[self.port1].streams[1],
                                self.ports[self.port1].streams[1].read_stats('totalFrames')))
        print('++++')

    def testStatsConfig(self):
        self._reserve_ports()

        port_stats = IxePortsStats(self.ixia.session)
        port_stats.set_attributes(enableArpStats=False)
