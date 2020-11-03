"""
IxExplorer samples. Samples require actual Ixia chassis and active ports.

Test setup:
Two Ixia ports connected back to back.

@author yoram@ignissoft.com
"""

import time
import json
from pathlib import Path
from typing import List

import pytest

from ixexplorer.ixe_app import IxeApp
from ixexplorer.ixe_port import StreamWarningsError
from ixexplorer.ixe_statistics_view import IxePortsStats, IxeStreamsStats, IxeCapFileFormat

from .test_base import _load_configs

def test_build_config(ixia: IxeApp, locations: List[str]) -> None:
    """ Build configuration from factory default and test different configuration objects. """
    print(test_build_config.__doc__)

    ixia.session.reserve_ports(locations, force=True)

    ixia.session.ports[locations[0]].add_stream()
    ixia.session.ports[locations[0]].streams[1].da = "22:22:22:22:22:11"
    ixia.session.ports[locations[0]].streams[1].sa = "11:11:11:11:11:11"
    ixia.session.ports[locations[0]].add_stream(name='aaa')
    ixia.session.ports[locations[0]].streams[2].da = "22:22:22:22:22:22"
    ixia.session.ports[locations[0]].streams[2].sa = "11:11:11:11:11:22"
    ixia.session.ports[locations[0]].add_stream(name='1 a')
    ixia.session.ports[locations[0]].add_stream(name='1-a')
    ixia.session.ports[locations[0]].add_stream(name='1/a')
    ixia.session.ports[locations[0]].add_stream(name='1%a')
    ixia.session.ports[locations[0]].add_stream(name='1\a')
    ixia.session.ports[locations[0]].write()

    assert ixia.session.ports[locations[0]].streams[1].da == '22:22:22:22:22:11'
    assert ixia.session.ports[locations[0]].streams[1].sa == '11:11:11:11:11:11'
    assert ixia.session.ports[locations[0]].streams[2].da == '22:22:22:22:22:22'
    assert ixia.session.ports[locations[0]].streams[2].sa == '11:11:11:11:11:22'
    assert ixia.session.ports[locations[0]].streams[3].name == '1 a'
    assert ixia.session.ports[locations[0]].streams[4].name == '1-a'
    assert ixia.session.ports[locations[0]].streams[5].name == '1/a'
    assert ixia.session.ports[locations[0]].streams[6].name == '1%a'
    assert ixia.session.ports[locations[0]].streams[7].name == '1\a'

    ixia.session.ports[locations[1]].add_stream()
    ixia.session.ports[locations[1]].streams[1].da = '11:11:11:11:11:11'
    ixia.session.ports[locations[1]].streams[1].sa = '22:22:22:22:22:11'
    ixia.session.ports[locations[1]].add_stream()
    ixia.session.ports[locations[1]].streams[2].da = '11:11:11:11:11:22'
    ixia.session.ports[locations[1]].streams[2].sa = '22:22:22:22:22:22'
    ixia.session.ports[locations[1]].write()

    assert ixia.session.ports[locations[0]].streams[1].da == '22:22:22:22:22:11'
    assert ixia.session.ports[locations[0]].streams[1].sa == '11:11:11:11:11:11'
    assert ixia.session.ports[locations[0]].streams[2].da == '22:22:22:22:22:22'
    assert ixia.session.ports[locations[0]].streams[2].sa == '11:11:11:11:11:22'


def test_port_stats(ixia: IxeApp, locations: List[str]) -> None:
    """ Test port statistics. """
    print(test_port_stats.__doc__)

    ixia.session.reserve_ports(locations, force=True)
    cfg1 = Path(__file__).parent.joinpath('configs/test_config_1.prt')
    cfg2 = Path(__file__).parent.joinpath('configs/test_config_2.prt')
    _load_configs(ixia, cfg1, cfg2)

    port1 = locations[0]
    port2 = locations[1]

    ixia.session.start_transmit()
    port_stats = IxePortsStats()
    port_stats.read_stats()
    print(json.dumps(port_stats.statistics, indent=1, sort_keys=True))
    assert port_stats.statistics[port1]['framesSent'] > 0
    assert port_stats.statistics[port2]['framesSent_rate'] > 0
    ixia.session.stop_transmit()

    ixia.session.ports[port1].start_transmit()
    time.sleep(8)
    ixia.session.ports[port1].stop_transmit()
    time.sleep(1)
    port1_stats = ixia.session.ports[port1].read_stats('framesSent', 'framesReceived')
    print(json.dumps(port1_stats, indent=1))
    assert port1_stats['framesSent'] > 0
    assert port1_stats['framesSent_rate'] == 0


def test_stream_stats(ixia: IxeApp, locations: List[str]) -> None:
    """ Test stream statistics. """
    print(test_stream_stats.__doc__)

    ixia.session.reserve_ports(locations, force=True)
    cfg1 = Path(__file__).parent.joinpath('configs/test_config_1.prt')
    cfg2 = Path(__file__).parent.joinpath('configs/test_config_2.prt')
    _load_configs(ixia, cfg1, cfg2)

    port1 = locations[0]
    port2 = locations[1]

    ixia.session.start_transmit()
    time.sleep(2)
    ixia.session.stop_transmit()

    stream_stats = IxeStreamsStats()
    ixia.session.ports[port1].streams[1].rx_ports = [ixia.session.ports[port2]]
    ixia.session.ports[port1].streams[2].rx_ports = [ixia.session.ports[port2]]
    ixia.session.ports[port2].rx_ports = ixia.session.ports[port1]
    stream_stats.read_stats()
    print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))
    assert stream_stats.statistics[str(ixia.session.ports[port1].streams[1])]['tx']['framesSent'] > 0
    assert stream_stats.statistics[str(ixia.session.ports[port1].streams[1])]['tx']['frameRate'] == 0
    assert stream_stats.statistics[str(ixia.session.ports[port1].streams[1])]['rx']['totalFrames'] > 0
    assert stream_stats.statistics[str(ixia.session.ports[port1].streams[1])]['rx']['frameRate'] == 0

    print(json.dumps(ixia.session.ports[port1].read_stream_stats('totalFrames'), indent=1))
    print(json.dumps(ixia.session.ports[port1].streams[1].read_stats('totalFrames'), indent=1))


def test_capture(ixia: IxeApp, locations: List[str]) -> None:

    ixia.session.reserve_ports(locations, force=True)
    cfg1 = Path(__file__).parent.joinpath('configs/cap_config.prt')
    cfg2 = Path(__file__).parent.joinpath('configs/cap_config.prt')
    _load_configs(ixia, cfg1, cfg2)

    port1 = locations[0]
    port2 = locations[1]

    ixia.session.ports[port1].start_capture()
    ixia.session.ports[port2].start_transmit(blocking=True)
    # Order matters to make sure nPackets is refreshed, so we read port2, port1 and then port1, port2
    num_packets = ixia.session.ports[port2].stop_capture()
    assert num_packets == 0
    assert not ixia.session.ports[port1].get_cap_file()
    num_packets = ixia.session.ports[port1].stop_capture()
    assert num_packets == 800
    assert not ixia.session.ports[port2].get_cap_file()
    print(ixia.session.ports[port1].get_cap_frames(1, 3, 5))

    ixia.session.ports[port1].clear_all_stats()
    ixia.session.ports[port2].clear_all_stats()

    ixia.session.start_capture()
    ixia.session.start_transmit()
    ixia.session.stop_transmit()
    num_packets = ixia.session.stop_capture(cap_file_name='c:/temp/ixia__session_cap',
                                            cap_file_format=IxeCapFileFormat.txt)
    for name, port in ixia.session.ports.items():
        assert num_packets[port] < 800
        print(name)
        print(port.cap_file_name)
        print(port.get_cap_file())


def test_capture_content(ixia: IxeApp, locations: List[str]) -> None:

    ixia.session.reserve_ports(locations, force=True)

    port1 = locations[0]
    port2 = locations[1]

    ixia.session.ports[port1].loopback = 1
    ixia.session.ports[port1].add_stream()
    ixia.session.ports[port1].streams[1].sa = "11:11:11:11:11:11"
    ixia.session.ports[port1].streams[1].dma = 2
    ixia.session.ports[port1].streams[1].numFrames = 1
    ixia.session.ports[port1].write()
    ixia.session.start_capture()
    ixia.session.start_transmit(blocking=True)
    ixia.session.stop_capture()
    assert "11 11 11 11 11 11" in str(ixia.session.ports[port2].get_cap_frames(1))

    ixia.session.ports[port1].streams[1].sa = "22:22:22:22:22:22"
    ixia.session.ports[port1].streams[1].numFrames = 2
    ixia.session.ports[port1].write()
    ixia.session.start_capture()
    ixia.session.start_transmit(blocking=True)
    ixia.session.stop_capture()
    assert "11 11 11 11 11 11" not in str(ixia.session.ports[port2].get_cap_frames(2))
    assert "22 22 22 22 22 22" in str(ixia.session.ports[port2].get_cap_frames(2))


def test_long_capture(ixia: IxeApp, locations: List[str]) -> None:

    ixia.session.reserve_ports(locations, force=True)
    cfg1 = Path(__file__).parent.joinpath('configs/long_frame_config.prt')
    cfg2 = Path(__file__).parent.joinpath('configs/long_frame_config.prt')
    try:
        _load_configs(ixia, cfg1, cfg2)
    except StreamWarningsError as _:
        pass

    ixia.session.start_capture()
    ixia.session.start_transmit(blocking=True)
    ixia.session.stop_capture(cap_file_name=None, cap_file_format=IxeCapFileFormat.mem)
    for p in range(1, ixia.session.ports[locations[1]].capture.nPackets + 1):
        print('frame len = {}'.format(len(ixia.session.ports[locations[1]].get_cap_frames(p)[0]) / 3 + 1))


def test_stream_stats_abstract_layer_all_ports(ixia: IxeApp, locations: List[str]) -> None:

    port1 = locations[0]
    port2 = locations[1]

    stats = _config_and_run_stream_stats_test(ixia, locations, rx_ports=[])

    assert stats[str(ixia.session.ports[port1].streams[1])]['tx']['framesSent'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == -1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['sequenceGaps'] == 0

    assert stats[str(ixia.session.ports[port2].streams[2])]['tx']['framesSent'] == 4
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == -1
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == 4


def test_stream_stats_abstract_layer_single_rx_port(ixia: IxeApp, locations: List[str]) -> None:

    port1 = locations[0]
    port2 = locations[1]

    stats = _config_and_run_stream_stats_test(ixia, locations, rx_ports=[port1])

    assert stats[str(ixia.session.ports[port1].streams[1])]['tx']['framesSent'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == -1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == -1

    assert stats[str(ixia.session.ports[port2].streams[2])]['tx']['framesSent'] == 4
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == -1
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == 4


def test_stream_stats_abstract_layer_flags(ixia: IxeApp, locations: List[str]) -> None:

    port1 = locations[0]
    port2 = locations[1]

    stats = _config_and_run_stream_stats_test(ixia, locations, rx_ports=[], sc=False, di=False, ts=False)

    assert stats[str(ixia.session.ports[port1].streams[1])]['tx']['framesSent'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == -1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['sequenceGaps'] == -1

    assert stats[str(ixia.session.ports[port2].streams[2])]['tx']['framesSent'] == 4
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == -1
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == 4


def test_prbs(ixia: IxeApp, locations: List[str]) -> None:

    port1 = locations[0]
    port2 = locations[1]

    stats = _config_and_run_stream_stats_test(ixia, locations, rx_ports=[])

    assert stats[str(ixia.session.ports[port1].streams[1])]['tx']['framesSent'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['minLatency'] != -1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['prbsBerRatio'] == -1
    assert stats[str(ixia.session.ports[port2].streams[2])]['tx']['framesSent'] == 4
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == 4
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['minLatency'] != -1
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['prbsBerRatio'] == -1

    ixia.session.set_prbs()
    # For coverage we call port.wait_for_up instead of session.wait_for_up.
    ixia.session.ports[port1].wait_for_up()
    ixia.session.ports[port2].wait_for_up()

    ixia.session.clear_all_stats()
    ixia.session.start_transmit()
    time.sleep(2)
    ixia.session.stop_transmit()
    time.sleep(2)

    stream_stats = IxeStreamsStats(ixia.session)
    stream_stats.read_stats()
    print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))
    stats = stream_stats.statistics

    for port in ixia.session.ports.values():
        if not int(port.isValidFeature('portFeaturePrbs')):
            pytest.skip('Port not supporting Prbs')

    assert stats[str(ixia.session.ports[port1].streams[1])]['tx']['framesSent'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['minLatency'] == -1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['prbsBerRatio'] != -1
    assert stats[str(ixia.session.ports[port2].streams[2])]['tx']['framesSent'] == 4
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == 4
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['minLatency'] == -1
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['prbsBerRatio'] != -1


def test_clear_all_stats(ixia: IxeApp, locations: List[str]) -> None:

    port1 = locations[0]
    port2 = locations[1]

    stats = _config_and_run_stream_stats_test(ixia, locations, rx_ports=[])

    assert stats[str(ixia.session.ports[port1].streams[1])]['tx']['framesSent'] == 1
    assert stats[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == 1
    assert stats[str(ixia.session.ports[port2].streams[2])]['tx']['framesSent'] == 4
    assert stats[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == 4

    port_stats = IxePortsStats(ixia.session)
    stream_stats = IxeStreamsStats(ixia.session)

    port_stats.read_stats('framesSent')
    print(json.dumps(port_stats.statistics, indent=1, sort_keys=True))
    assert port_stats.statistics[str(ixia.session.ports[port1])]['framesSent'] == 3
    assert port_stats.statistics[str(ixia.session.ports[port2])]['framesSent'] == 7

    ixia.session.ports[port1].clear_port_stats()
    time.sleep(2)
    port_stats.read_stats('framesSent')
    print(json.dumps(port_stats.statistics, indent=1, sort_keys=True))
    assert port_stats.statistics[str(ixia.session.ports[port1])]['framesSent'] == 0
    assert port_stats.statistics[str(ixia.session.ports[port2])]['framesSent'] == 7
    stream_stats.read_stats('totalFrames')
    print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))
    stream_1_rx = stream_stats.statistics[str(ixia.session.ports[port1].streams[1])]['rx']
    assert stream_stats.statistics[str(ixia.session.ports[port1].streams[1])]['tx']['framesSent'] == 0
    assert stream_1_rx[str(ixia.session.ports[port2])]['totalFrames'] == 1  # noqa
    assert stream_stats.statistics[str(ixia.session.ports[port2].streams[2])]['tx']['framesSent'] == 4
    assert stream_1_rx[str(ixia.session.ports[port1])]['totalFrames'] == -1  # noqa

    ixia.session.clear_all_stats()
    time.sleep(2)
    port_stats.read_stats('framesSent')
    print(json.dumps(port_stats.statistics, indent=1, sort_keys=True))
    assert port_stats.statistics[str(ixia.session.ports[port1])]['framesSent'] == 0
    assert port_stats.statistics[str(ixia.session.ports[port2])]['framesSent'] == 0
    stream_stats.read_stats('totalFrames')
    print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))
    assert stream_stats.statistics[str(ixia.session.ports[port1].streams[1])]['tx']['framesSent'] == 0
    assert stream_stats.statistics[str(ixia.session.ports[port1].streams[1])]['rx'][str(ixia.session.ports[port2])]['totalFrames'] == -1  # noqa
    assert stream_stats.statistics[str(ixia.session.ports[port2].streams[2])]['tx']['framesSent'] == 0
    assert stream_stats.statistics[str(ixia.session.ports[port2].streams[2])]['rx'][str(ixia.session.ports[port1])]['totalFrames'] == -1  # noqa


def _config_and_run_stream_stats_test(ixia: IxeApp, locations: List[str], rx_ports, sc=True, di=True, ts=True):

    ixia.session.reserve_ports(locations, force=True)

    iteration = 1
    for port_name in locations:
        port = ixia.session.ports[port_name]
        port.add_stream()
        port.add_stream()
        for stream in port.streams.values():
            stream.framesize = 68
            stream.vlan.vlanId = 33
            stream.dma = 'advance'
            stream.numFrames = iteration
            stream.rateMode = 'streamRateModeFps'
            iteration += 1

    ixia.session.set_stream_stats(rx_ports=[ixia.session.ports[r] for r in rx_ports],
                                  sequence_checking=sc, data_integrity=di, timestamp=ts)
    ixia.session.wait_for_up(ports=ixia.session.ports.values())

    ixia.session.start_transmit()
    time.sleep(2)
    ixia.session.stop_transmit()
    time.sleep(2)

    stream_stats = IxeStreamsStats(ixia.session)
    stream_stats.read_stats()
    print(json.dumps(stream_stats.statistics, indent=1, sort_keys=True))

    return stream_stats.statistics
