"""
TestCenter package tests that require actual Ixia chassis and active ports.

Test setup:
Two Ixia ports connected back to back.

@author yoram@ignissoft.com
"""

from os import path
import time
import json

from ixexplorer.ixe_statistics_view import IxePortsStats, IxeStreamsStats, IxeCapFileFormat
from ixexplorer.test.test_base import IxeTestBase
from ixexplorer.ixe_port import StreamWarningsError, IxeTransmitMode


class IxeTestOnline(IxeTestBase):

    def testPortStats(self):
        cfg1 = path.join(path.dirname(__file__), 'configs/stats_config_1.prt')
        cfg2 = path.join(path.dirname(__file__), 'configs/stats_config_2.prt')
        self._reserver_and_load(cfg1, cfg2)

        self.ixia.session.start_transmit()
        port_stats = IxePortsStats(self.ixia.session)
        port_stats.read_stats()
        print(json.dumps(port_stats.statistics, indent=1, sort_keys=True))
        assert(port_stats.statistics[self.port1]['framesSent'] > 0)
        assert(port_stats.statistics[self.port2]['framesSent_rate'] > 0)
        self.ixia.session.stop_transmit()

        self.ports[self.port1].start_transmit()
        time.sleep(4)
        self.ports[self.port1].stop_transmit()
        port1_stats = self.ports[self.port1].read_stats('framesSent', 'framesReceived')
        print(json.dumps(port1_stats, indent=1))
        assert(port1_stats['framesSent'] > 0)
        assert(port1_stats['framesSent_rate'] == 0)

    def testStreamStats(self):
        cfg1 = path.join(path.dirname(__file__), 'configs/stats_config_1.prt')
        cfg2 = path.join(path.dirname(__file__), 'configs/stats_config_2.prt')
        self._reserver_and_load(cfg1, cfg2)

        self.ixia.session.start_transmit()
        time.sleep(2)
        self.ixia.session.stop_transmit()

        stream_stats = IxeStreamsStats(self.ixia.session)
        self.ports[self.port1].streams[1].rx_ports = [self.ports[self.port2]]
        self.ports[self.port1].streams[2].rx_ports = [self.ports[self.port2]]
        self.ports[self.port2].rx_ports = self.ports[self.port1]
        stream_stats.read_stats()
        print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))
        assert(stream_stats.statistics[str(self.ports[self.port1].streams[1])]['tx']['framesSent'] > 0)
        assert(stream_stats.statistics[str(self.ports[self.port1].streams[1])]['tx']['frameRate'] == 0)
        assert(stream_stats.statistics[str(self.ports[self.port1].streams[1])]['rx']['totalFrames'] > 0)
        assert(stream_stats.statistics[str(self.ports[self.port1].streams[1])]['rx']['frameRate'] == 0)

        print(json.dumps(self.ports[self.port1].read_stream_stats('totalFrames'), indent=1))
        print(json.dumps(self.ports[self.port1].streams[1].read_stats('totalFrames'), indent=1))

    def testCapture(self):
        cfg1 = path.join(path.dirname(__file__), 'configs/cap_config.prt')
        cfg2 = path.join(path.dirname(__file__), 'configs/cap_config.prt')
        self._reserver_and_load(cfg1, cfg2)

        self.ports[self.port1].start_capture()
        self.ports[self.port2].start_transmit(blocking=True)
        # Order matters to make sure nPackets is refreshed, so we read port2, port1 and then port1, port2
        nPackets = self.ports[self.port2].stop_capture()
        assert(nPackets == 0)
        assert(not self.ports[self.port1].get_cap_file())
        nPackets = self.ports[self.port1].stop_capture()
        assert(nPackets == 800)
        assert(not self.ports[self.port2].get_cap_file())
        print(self.ports[self.port1].get_cap_frames(1, 3, 5))

        self.ports[self.port1].clear_stats()
        self.ports[self.port2].clear_stats()

        self.ixia.session.start_capture()
        self.ixia.session.start_transmit()
        self.ixia.session.stop_transmit()
        nPackets = self.ixia.session.stop_capture(cap_file_name='c:/temp/ixia__session_cap',
                                                  cap_file_format=IxeCapFileFormat.txt)
        for name, port in self.ports.items():
            assert(nPackets[port] < 800)
            print(name)
            print(port.cap_file_name)
            print(port.get_cap_file())

    def testCaptureContent(self):
        self._reserve_ports(self.port1, self.port2)

        self.ports[self.port1].loopback = 1
        self.ports[self.port1].add_stream()
        self.ports[self.port1].streams[1].sa = "11:11:11:11:11:11"
        self.ports[self.port1].streams[1].dma = 2
        self.ports[self.port1].streams[1].numFrames = 1
        self.ports[self.port1].write()
        self.ixia.session.start_capture()
        self.ixia.session.start_transmit(blocking=True)
        self.ixia.session.stop_capture()
        assert("11 11 11 11 11 11" in str(self.ports[self.port1].get_cap_frames(1)))

        self.ports[self.port1].streams[1].sa = "22:22:22:22:22:22"
        self.ports[self.port1].streams[1].numFrames = 2
        self.ports[self.port1].write()
        self.ixia.session.start_capture()
        self.ixia.session.start_transmit(blocking=True)
        self.ixia.session.stop_capture()
        assert("11 11 11 11 11 11" not in str(self.ports[self.port1].get_cap_frames(2)))
        assert("22 22 22 22 22 22" in str(self.ports[self.port1].get_cap_frames(2)))

    def testLongCapture(self):
        cfg1 = path.join(path.dirname(__file__), 'configs/long_frame_config.prt')
        cfg2 = path.join(path.dirname(__file__), 'configs/long_frame_config.prt')
        try:
            self._reserver_and_load(cfg1, cfg2)
        except StreamWarningsError as _:
            pass

        self.ixia.session.start_capture()
        self.ixia.session.start_transmit(blocking=True)
        self.ixia.session.stop_capture(cap_file_name=None, cap_file_format=IxeCapFileFormat.mem)
        for p in range(1, self.ports[self.port2].capture.nPackets + 1):
            print('frame len = {}'.format(len(self.ports[self.port2].get_cap_frames(p)[0]) / 3 + 1))

    def testStreamStatsAbstractLayer(self):

        self._reserve_ports(self.port1)

        port = self.ports[self.port1]
        port.loopback = 'portLoopback'
        port.transmitMode = IxeTransmitMode.advancedScheduler
        port.add_stream('yoram')
        port.add_stream()
        for stream in port.streams.values():
            stream.framesize = 64
            stream.dma = 'contPacket'
            stream.numFrames = 1000
            stream.rateMode = 'streamRateModeFps'

        self.ixia.session.set_stream_stats()

        self.ixia.session.start_transmit()
        time.sleep(2)
        print(json.dumps(port.streams[1].read_stats(), indent=1, sort_keys=True))
        self.ixia.session.stop_transmit()

        stream_stats = IxeStreamsStats(self.ixia.session)
        stream_stats.read_stats()
        print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))
