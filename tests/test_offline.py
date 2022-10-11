"""
ixexplorer package tests that can run in offline mode.
"""
import json
from pathlib import Path
from typing import List

import pytest

from ixexplorer.ixe_app import IxeApp
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_port import IxePortCpu, IxeReceiveMode
from tests import _load_configs


def test_hello_world(ixia: IxeApp) -> None:
    """Verify setup and connectivity."""


def test_clear(ixia: IxeApp, locations: List[str]) -> None:
    """Test clear ports without reservation."""
    for port in ixia.session.add_ports(*locations).values():
        port.release(force=True)
        port.clear(stats=False)
        IxePortCpu(port).reset_cpu()


def test_load_config(ixia: IxeApp, locations: List[str]) -> None:
    """Load configuration and test different configuration objects."""
    ixia.session.add_ports(*locations)
    ixia.session.reserve_ports(force=True)
    cfg1 = Path(__file__).parent.joinpath("configs/test_config_1.prt")
    cfg2 = Path(__file__).parent.joinpath("configs/test_config_1.prt")
    _load_configs(ixia, cfg1, cfg2)

    assert len(ixia.session.ports) == 2
    assert len(ixia.session.ports[locations[0]].streams) == 2
    assert len(ixia.session.ports[locations[1]].streams) == 2

    assert ixia.session.ports[locations[0]].streams[1].da == "22:22:22:22:22:11"
    assert ixia.session.ports[locations[0]].streams[1].sa == "11:11:11:11:11:11"
    assert ixia.session.ports[locations[0]].streams[2].da == "22:22:22:22:22:22"
    assert ixia.session.ports[locations[0]].streams[2].sa == "11:11:11:11:11:22"

    ixia.session.ports[locations[0]].streams[1].da = "33:33:33:33:33:33"
    ixia.session.ports[locations[0]].streams[1].sa = "44:44:44:44:44:44"
    ixia.session.ports[locations[0]].streams[2].ip.ix_get(force=True)
    ixia.session.ports[locations[0]].streams[2].ip.destIpAddr = "2.2.2.2"
    ixia.session.ports[locations[0]].write()

    print(json.dumps(ixia.session.ports[locations[0]].get_attributes(), indent=2))
    print(json.dumps(ixia.session.ports[locations[0]].streams[1].get_attributes(), indent=2))

    ixia.refresh()
    assert ixia.session.ports[locations[0]].streams[2].da == "22:22:22:22:22:22"
    assert ixia.session.ports[locations[0]].streams[2].sa == "11:11:11:11:11:22"
    assert ixia.session.ports[locations[0]].streams[1].da == "33:33:33:33:33:33"
    assert ixia.session.ports[locations[0]].streams[1].sa == "44:44:44:44:44:44"


def test_build_config(ixia: IxeApp, locations: List[str]) -> None:
    """Build configuration from factory default and test different configuration objects."""
    print(test_build_config.__doc__)

    ixia.session.reserve_ports(locations, force=True)

    ixia.session.ports[locations[0]].add_stream()
    ixia.session.ports[locations[0]].streams[1].da = "22:22:22:22:22:11"
    ixia.session.ports[locations[0]].streams[1].sa = "11:11:11:11:11:11"
    ixia.session.ports[locations[0]].add_stream(name="aaa")
    ixia.session.ports[locations[0]].streams[2].da = "22:22:22:22:22:22"
    ixia.session.ports[locations[0]].streams[2].sa = "11:11:11:11:11:22"
    ixia.session.ports[locations[0]].add_stream(name="1 a")
    ixia.session.ports[locations[0]].add_stream(name="1-a")
    ixia.session.ports[locations[0]].add_stream(name="1/a")
    ixia.session.ports[locations[0]].add_stream(name="1%a")
    ixia.session.ports[locations[0]].add_stream(name="1\a")
    ixia.session.ports[locations[0]].write()

    assert ixia.session.ports[locations[0]].streams[1].da == "22:22:22:22:22:11"
    assert ixia.session.ports[locations[0]].streams[1].sa == "11:11:11:11:11:11"
    assert ixia.session.ports[locations[0]].streams[2].da == "22:22:22:22:22:22"
    assert ixia.session.ports[locations[0]].streams[2].sa == "11:11:11:11:11:22"
    assert ixia.session.ports[locations[0]].streams[3].name == "1 a"
    assert ixia.session.ports[locations[0]].streams[4].name == "1-a"
    assert ixia.session.ports[locations[0]].streams[5].name == "1/a"
    assert ixia.session.ports[locations[0]].streams[6].name == "1%a"
    assert ixia.session.ports[locations[0]].streams[7].name == "1\a"

    ixia.session.ports[locations[1]].add_stream()
    ixia.session.ports[locations[1]].streams[1].da = "11:11:11:11:11:11"
    ixia.session.ports[locations[1]].streams[1].sa = "22:22:22:22:22:11"
    ixia.session.ports[locations[1]].add_stream()
    ixia.session.ports[locations[1]].streams[2].da = "11:11:11:11:11:22"
    ixia.session.ports[locations[1]].streams[2].sa = "22:22:22:22:22:22"
    ixia.session.ports[locations[1]].write()

    assert ixia.session.ports[locations[0]].streams[1].da == "22:22:22:22:22:11"
    assert ixia.session.ports[locations[0]].streams[1].sa == "11:11:11:11:11:11"
    assert ixia.session.ports[locations[0]].streams[2].da == "22:22:22:22:22:22"
    assert ixia.session.ports[locations[0]].streams[2].sa == "11:11:11:11:11:22"


def test_write_after_write(ixia: IxeApp, locations: List[str]) -> None:
    """Test port configuration write to HW."""
    print(test_write_after_write.__doc__)

    ixia.session.reserve_ports(locations, force=True)

    IxeObject.set_auto_set(False)

    ixia.session.ports[locations[0]].loopback = 1
    ixia.session.ports[locations[0]].add_stream()
    port1_stream1 = ixia.session.ports[locations[0]].streams[1]
    port1_stream1.da = "22:22:22:22:22:11"
    port1_stream1.sa = "11:11:11:11:11:11"
    port1_stream1.ip.destIpAddr = "1.1.2.1"
    port1_stream1.ip.sourceIpAddr = "1.1.1.1"
    port1_stream1.ip.ipProtocol = "17"
    port1_stream1.ip.ix_set()

    ixia.session.ports[locations[0]].add_stream()
    port1_stream2 = ixia.session.ports[locations[0]].streams[2]
    port1_stream2.da = "22:22:22:22:22:22"
    port1_stream2.sa = "11:11:11:11:11:22"
    port1_stream2.ip.destIpAddr = "1.1.2.2"
    port1_stream2.ip.sourceIpAddr = "1.1.1.2"
    port1_stream2.ip.ipProtocol = "17"
    port1_stream2.ip.ix_set()
    ixia.session.ports[locations[0]].write()

    ixia.session.ports[locations[0]].add_stream()
    port1_stream3 = ixia.session.ports[locations[0]].streams[3]
    port1_stream3.da = "22:22:22:22:22:33"
    port1_stream3.sa = "11:11:11:11:11:33"
    port1_stream3.ip.destIpAddr = "1.1.2.3"
    port1_stream3.ip.sourceIpAddr = "1.1.1.3"
    port1_stream3.ip.ipProtocol = "17"
    port1_stream3.ip.ix_set()
    ixia.session.ports[locations[0]].write()

    IxeObject.set_auto_set(True)

    ixia.session.ports[locations[1]].add_stream()
    port2_stream1 = ixia.session.ports[locations[1]].streams[1]
    port2_stream1.set_attributes(da="11:11:11:11:11:11", sa="22:22:22:22:22:11")
    port2_stream1.ip.set_attributes(destIpAddr="1.1.1.2", sourceIpAddr="1.1.2.2", ipProtocol="17")
    ixia.session.ports[locations[1]].write()

    assert port1_stream1.da == "22:22:22:22:22:11"
    assert port1_stream1.ip.destIpAddr == "1.1.2.1"
    assert port2_stream1.da == "11:11:11:11:11:11"
    assert port2_stream1.ip.destIpAddr == "1.1.1.2"


def test_discover(ixia: IxeApp, locations: List[str]) -> None:
    """Test chassis discovery."""
    print(test_discover.__doc__)

    chassis = list(ixia.chassis_chain.values())[0]
    assert chassis.obj_name() == chassis.ipAddress
    ixia.discover()
    assert len(chassis.cards) > 0
    assert len(list(chassis.cards.values())[0].ports) > 0
    print(list(list(chassis.cards.values())[0].ports.values())[0].supported_speeds())


def test_stream_stats_configuration(ixia: IxeApp, locations: List[str]) -> None:
    """Test stream statistics configuration (without running actual traffic)."""
    print(test_stream_stats_configuration.__doc__)

    ixia.session.reserve_ports(locations, force=True)

    #: :type port: ixexplorer.ixe_port.IxePort
    port = ixia.session.ports[locations[0]]
    if not int(port.isValidFeature("portFeatureRxDataIntegrity")):
        pytest.skip("Port not supporting RxDataIntegrity")

    #: :type stream: ixexplorer.ixe_stream.IxeStream
    stream = port.add_stream()
    stream.framesize = 200

    assert port.autoDetectInstrumentation.signature == "87 73 67 49 42 87 11 80 08 71 18 05"
    assert stream.autoDetectInstrumentation.signature == "87 73 67 49 42 87 11 80 08 71 18 05"
    assert port.packetGroup.groupIdOffset == 52
    assert stream.packetGroup.groupIdOffset == 52
    assert port.dataIntegrity.signatureOffset == 40
    assert stream.dataIntegrity.signatureOffset == 40

    port.receiveMode = IxeReceiveMode.widePacketGroup.value | IxeReceiveMode.dataIntegrity.value
    stream.packetGroup.insertSignature = True
    stream.dataIntegrity.insertSignature = True

    port.autoDetectInstrumentation.signature = "{87 73 67 49 42 87 11 80 08 71 00 11}"
    stream.autoDetectInstrumentation.signature = "{87 73 67 49 42 87 11 80 08 71 00 11}"
    port.packetGroup.groupIdOffset = 152
    stream.packetGroup.groupIdOffset = 152
    port.dataIntegrity.signatureOffset = 140
    stream.dataIntegrity.signatureOffset = 140

    port.packetGroup.groupIdMode = "packetGroupSplit"

    port.write()
    ixia.refresh()

    print(json.dumps(port.autoDetectInstrumentation.get_attributes(), indent=2))
    print(json.dumps(port.packetGroup.get_attributes(), indent=2))
    print(json.dumps(port.splitPacketGroup.get_attributes(), indent=2))
    print(json.dumps(port.dataIntegrity.get_attributes(), indent=2))
    print(json.dumps(stream.autoDetectInstrumentation.get_attributes(), indent=2))
    print(json.dumps(stream.packetGroup.get_attributes(), indent=2))
    print(json.dumps(stream.dataIntegrity.get_attributes(), indent=2))

    assert port.autoDetectInstrumentation.signature == "87 73 67 49 42 87 11 80 08 71 00 11"
    assert stream.autoDetectInstrumentation.signature == "87 73 67 49 42 87 11 80 08 71 00 11"
    assert port.packetGroup.groupIdOffset == 152
    assert stream.packetGroup.groupIdOffset == 152
    assert port.dataIntegrity.signatureOffset == 140
    assert stream.dataIntegrity.signatureOffset == 140


def test_wrf(ixia: IxeApp, locations: List[str]) -> None:
    """Test weighted random frame size configuration."""
    print(test_wrf.__doc__)

    ixia.session.reserve_ports(locations, force=True)

    port = ixia.session.ports[locations[0]]
    port.add_stream()
    port.add_stream()
    port.add_stream()
    for stream in port.streams.values():
        stream.frameSizeType = 1
        stream.weightedRandomFramesize.ix_set_default()
        stream.weightedRandomFramesize.randomType = 1
        stream.weightedRandomFramesize.addPair(64, 6)
        stream.weightedRandomFramesize.addPair(70, 7)
        stream.weightedRandomFramesize.addPair(80, 8)
        stream.weightedRandomFramesize.delPair(64, 1)
        stream.write()
    port.write()
