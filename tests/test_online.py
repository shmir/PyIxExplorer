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
from test_base import TestIxeBase
from ixexplorer.ixe_port import StreamWarningsError


class TestIxeOnline(TestIxeBase):

    def test_port_stats(self):
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
        time.sleep(8)
        self.ports[self.port1].stop_transmit()
        time.sleep(1)
        port1_stats = self.ports[self.port1].read_stats('framesSent', 'framesReceived')
        print(json.dumps(port1_stats, indent=1))
        assert(port1_stats['framesSent'] > 0)
        assert(port1_stats['framesSent_rate'] == 0)

    def test_stream_stats(self):
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

    def test_capture(self):
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

        self.ports[self.port1].clear_all_stats()
        self.ports[self.port2].clear_all_stats()

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

    def test_capture_content(self):
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
        assert("11 11 11 11 11 11" in str(self.ports[self.port2].get_cap_frames(1)))

        self.ports[self.port1].streams[1].sa = "22:22:22:22:22:22"
        self.ports[self.port1].streams[1].numFrames = 2
        self.ports[self.port1].write()
        self.ixia.session.start_capture()
        self.ixia.session.start_transmit(blocking=True)
        self.ixia.session.stop_capture()
        assert("11 11 11 11 11 11" not in str(self.ports[self.port2].get_cap_frames(2)))
        assert("22 22 22 22 22 22" in str(self.ports[self.port2].get_cap_frames(2)))

    def test_long_capture(self):
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

    def test_stream_stats_abstract_layer_all_ports(self):

        stats = self._config_and_run_stream_stats_test(rx_ports=[])

        assert(stats[str(self.ports[self.port1].streams[1])]['tx']['framesSent'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port1])]['totalFrames'] == -1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['totalFrames'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['sequenceGaps'] == 0)

        assert(stats[str(self.ports[self.port2].streams[2])]['tx']['framesSent'] == 4)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port2])]['totalFrames'] == -1)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['totalFrames'] == 4)

    def test_stream_stats_abstract_layer_single_rx_port(self):

        stats = self._config_and_run_stream_stats_test(rx_ports=[self.port1])

        assert(stats[str(self.ports[self.port1].streams[1])]['tx']['framesSent'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port1])]['totalFrames'] == -1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['totalFrames'] == -1)

        assert(stats[str(self.ports[self.port2].streams[2])]['tx']['framesSent'] == 4)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port2])]['totalFrames'] == -1)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['totalFrames'] == 4)

    def test_stream_stats_abstract_layer_flags(self):

        stats = self._config_and_run_stream_stats_test(rx_ports=[], sc=False, di=False, ts=False)

        assert(stats[str(self.ports[self.port1].streams[1])]['tx']['framesSent'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port1])]['totalFrames'] == -1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['totalFrames'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['sequenceGaps'] == -1)

        assert(stats[str(self.ports[self.port2].streams[2])]['tx']['framesSent'] == 4)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port2])]['totalFrames'] == -1)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['totalFrames'] == 4)

    def test_prbs(self):

        stats = self._config_and_run_stream_stats_test(rx_ports=[])

        assert(stats[str(self.ports[self.port1].streams[1])]['tx']['framesSent'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['totalFrames'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['minLatency'] != -1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['prbsBerRatio'] == -1)
        assert(stats[str(self.ports[self.port2].streams[2])]['tx']['framesSent'] == 4)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['totalFrames'] == 4)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['minLatency'] != -1)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['prbsBerRatio'] == -1)

        self.ixia.session.set_prbs()
        # For coverage we call port.wait_for_up instead of session.wait_for_up.
        self.ports[self.port1].wait_for_up()
        self.ports[self.port2].wait_for_up()

        self.ixia.session.clear_all_stats()
        self.ixia.session.start_transmit()
        time.sleep(2)
        self.ixia.session.stop_transmit()
        time.sleep(2)

        stream_stats = IxeStreamsStats(self.ixia.session)
        stream_stats.read_stats()
        print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))
        stats = stream_stats.statistics

        for port in self.ports.values():
            if not int(port.isValidFeature('portFeaturePrbs')):
                self.skipTest('Port not supporting Prbs')
                return

        assert(stats[str(self.ports[self.port1].streams[1])]['tx']['framesSent'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['totalFrames'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['minLatency'] == -1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['prbsBerRatio'] != -1)
        assert(stats[str(self.ports[self.port2].streams[2])]['tx']['framesSent'] == 4)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['totalFrames'] == 4)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['minLatency'] == -1)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['prbsBerRatio'] != -1)

    def test_clear_all_stats(self):

        stats = self._config_and_run_stream_stats_test(rx_ports=[])

        assert(stats[str(self.ports[self.port1].streams[1])]['tx']['framesSent'] == 1)
        assert(stats[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['totalFrames'] == 1)
        assert(stats[str(self.ports[self.port2].streams[2])]['tx']['framesSent'] == 4)
        assert(stats[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['totalFrames'] == 4)

        port_stats = IxePortsStats(self.ixia.session)
        stream_stats = IxeStreamsStats(self.ixia.session)

        port_stats.read_stats('framesSent')
        print(json.dumps(port_stats.statistics, indent=1, sort_keys=True))
        assert(port_stats.statistics[str(self.ports[self.port1])]['framesSent'] == 3)
        assert(port_stats.statistics[str(self.ports[self.port2])]['framesSent'] == 7)

        self.ports[self.port1].clear_port_stats()
        time.sleep(2)
        port_stats.read_stats('framesSent')
        print(json.dumps(port_stats.statistics, indent=1, sort_keys=True))
        assert(port_stats.statistics[str(self.ports[self.port1])]['framesSent'] == 0)
        assert(port_stats.statistics[str(self.ports[self.port2])]['framesSent'] == 7)
        stream_stats.read_stats('totalFrames')
        print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))
        assert(stream_stats.statistics[str(self.ports[self.port1].streams[1])]['tx']['framesSent'] == 0)
        assert(stream_stats.statistics[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['totalFrames'] == 1)  # noqa
        assert(stream_stats.statistics[str(self.ports[self.port2].streams[2])]['tx']['framesSent'] == 4)
        assert(stream_stats.statistics[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['totalFrames'] == -1)  # noqa

        self.ixia.session.clear_all_stats()
        time.sleep(2)
        port_stats.read_stats('framesSent')
        print(json.dumps(port_stats.statistics, indent=1, sort_keys=True))
        assert(port_stats.statistics[str(self.ports[self.port1])]['framesSent'] == 0)
        assert(port_stats.statistics[str(self.ports[self.port2])]['framesSent'] == 0)
        stream_stats.read_stats('totalFrames')
        print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))
        assert(stream_stats.statistics[str(self.ports[self.port1].streams[1])]['tx']['framesSent'] == 0)
        assert(stream_stats.statistics[str(self.ports[self.port1].streams[1])]['rx'][str(self.ports[self.port2])]['totalFrames'] == -1)  # noqa
        assert(stream_stats.statistics[str(self.ports[self.port2].streams[2])]['tx']['framesSent'] == 0)
        assert(stream_stats.statistics[str(self.ports[self.port2].streams[2])]['rx'][str(self.ports[self.port1])]['totalFrames'] == -1)  # noqa

    def _config_and_run_stream_stats_test(self, rx_ports, sc=True, di=True, ts=True):

        self._reserve_ports(self.port1, self.port2)

        iteration = 1
        for port_name in [self.port1, self.port2]:
            port = self.ports[port_name]
            port.add_stream()
            port.add_stream()
            for stream in port.streams.values():
                stream.framesize = 68
                stream.vlan.vlanId = 33
                stream.dma = 'advance'
                stream.numFrames = iteration
                stream.rateMode = 'streamRateModeFps'
                iteration += 1

        self.ixia.session.set_stream_stats(rx_ports=[self.ports[r] for r in rx_ports],
                                           sequence_checking=sc, data_integrity=di, timestamp=ts)
        self.ixia.session.wait_for_up(ports=self.ports.values())

        self.ixia.session.start_transmit()
        time.sleep(2)
        self.ixia.session.stop_transmit()
        time.sleep(2)

        stream_stats = IxeStreamsStats(self.ixia.session)
        stream_stats.read_stats()
        print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))

        return stream_stats.statistics
