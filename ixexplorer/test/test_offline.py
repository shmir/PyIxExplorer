"""
IxExplorer package tests that can run in offline mode.

@author yoram@ignissoft.com
"""

from os import path
import json
import pytest

from trafficgenerator.tgn_utils import TgnError

from ixexplorer.api.tclproto import TclError
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_port import IxeReceiveMode, StreamWarningsError
from ixexplorer.test.test_base import TestIxeBase


class TestIxeOffline(TestIxeBase):

    def test_load_config(self):

        cfg1 = path.join(path.dirname(__file__), 'configs/test_config_1.prt')
        cfg2 = path.join(path.dirname(__file__), 'configs/test_config_2.str')
        self._reserver_and_load(cfg1, cfg2)

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

        print(json.dumps(self.ports[self.port1].get_attributes(), indent=4))
        print(json.dumps(self.ports[self.port1].streams[1].get_attributes(), indent=4))

        self.ixia.refresh()
        assert(self.ports[self.port1].streams[2].da == '22:22:22:22:22:22')
        assert(self.ports[self.port1].streams[2].sa == '11:11:11:11:11:22')
        assert(self.ports[self.port1].streams[1].da == '33:33:33:33:33:33')
        assert(self.ports[self.port1].streams[1].sa == '44:44:44:44:44:44')

    def test_build_config(self):
        self._reserve_ports(self.port1, self.port2)

        self.ports[self.port1].add_stream()
        self.ports[self.port1].streams[1].da = "22:22:22:22:22:11"
        self.ports[self.port1].streams[1].sa = "11:11:11:11:11:11"
        self.ports[self.port1].add_stream(name='aaa')
        self.ports[self.port1].streams[2].da = "22:22:22:22:22:22"
        self.ports[self.port1].streams[2].sa = "11:11:11:11:11:22"
        self.ports[self.port1].add_stream(name='1 a')
        self.ports[self.port1].add_stream(name='1-a')
        self.ports[self.port1].add_stream(name='1/a')
        self.ports[self.port1].add_stream(name='1%a')
        self.ports[self.port1].add_stream(name='1\a')
        self.ports[self.port1].write()

        assert(self.ports[self.port1].streams[1].da == '22:22:22:22:22:11')
        assert(self.ports[self.port1].streams[1].sa == '11:11:11:11:11:11')
        assert(self.ports[self.port1].streams[2].da == '22:22:22:22:22:22')
        assert(self.ports[self.port1].streams[2].sa == '11:11:11:11:11:22')
        assert(self.ports[self.port1].streams[3].name == '1 a')
        assert(self.ports[self.port1].streams[4].name == '1-a')
        assert(self.ports[self.port1].streams[5].name == '1/a')
        assert(self.ports[self.port1].streams[6].name == '1%a')
        assert(self.ports[self.port1].streams[7].name == '1\a')

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

    def test_write_after_write(self):
        self._reserve_ports(self.port1, self.port2)
        port1 = self.ports[self.port1]
        port2 = self.ports[self.port2]

        IxeObject.set_auto_set(False)

        port1.loopback = 1
        port1.add_stream()
        port1_stream1 = port1.streams[1]
        port1_stream1.da = '22:22:22:22:22:11'
        port1_stream1.sa = '11:11:11:11:11:11'
        port1_stream1.ip.destIpAddr = '1.1.2.1'
        port1_stream1.ip.sourceIpAddr = '1.1.1.1'
        port1_stream1.ip.ipProtocol = '17'
        port1_stream1.ip.ix_set()

        port1.add_stream()
        port1_stream2 = port1.streams[2]
        port1_stream2.da = '22:22:22:22:22:22'
        port1_stream2.sa = '11:11:11:11:11:22'
        port1_stream2.ip.destIpAddr = '1.1.2.2'
        port1_stream2.ip.sourceIpAddr = '1.1.1.2'
        port1_stream2.ip.ipProtocol = '17'
        port1_stream2.ip.ix_set()
        port1.write()

        port1.add_stream()
        port1_stream3 = port1.streams[3]
        port1_stream3.da = '22:22:22:22:22:33'
        port1_stream3.sa = '11:11:11:11:11:33'
        port1_stream3.ip.destIpAddr = '1.1.2.3'
        port1_stream3.ip.sourceIpAddr = '1.1.1.3'
        port1_stream3.ip.ipProtocol = '17'
        port1_stream3.ip.ix_set()
        port1.write()

        IxeObject.set_auto_set(True)

        port2.add_stream()
        port2_stream1 = port2.streams[1]
        port2_stream1.set_attributes(da='11:11:11:11:11:11', sa='22:22:22:22:22:11')
        port2_stream1.ip.set_attributes(destIpAddr='1.1.1.2', sourceIpAddr='1.1.2.2', ipProtocol='17')
        port2.write()

        assert(port1_stream1.da == '22:22:22:22:22:11')
        assert(port1_stream1.ip.destIpAddr == '1.1.2.1')
        assert(port2_stream1.da == '11:11:11:11:11:11')
        assert(port2_stream1.ip.destIpAddr == '1.1.1.2')

    def test_discover(self):

        chassis = list(self.ixia.chassis_chain.values())[0]
        assert(chassis.obj_name() == chassis.ipAddress)
        self.ixia.discover()
        assert(len(chassis.cards) > 0)
        assert(len(list(chassis.cards.values())[0].ports) > 0)
        print(list(list(chassis.cards.values())[0].ports.values())[0].supported_speeds())

    def test_stream_stats_objects(self):

        self._reserve_ports(self.port1)

        #: :type port: ixexplorer.ixe_port.IxePort
        port = self.ports[self.port1]
        if not int(port.isValidFeature('portFeatureRxDataIntegrity')):
            pytest.skip('Port not supporting RxDataIntegrity')
            return

        #: :type stream: ixexplorer.ixe_stream.IxeStream
        stream = port.add_stream()
        stream.framesize = 200

        assert(port.autoDetectInstrumentation.signature == '87 73 67 49 42 87 11 80 08 71 18 05')
        assert(stream.autoDetectInstrumentation.signature == '87 73 67 49 42 87 11 80 08 71 18 05')
        assert(port.packetGroup.groupIdOffset == 52)
        assert(stream.packetGroup.groupIdOffset == 52)
        assert(port.dataIntegrity.signatureOffset == 40)
        assert(stream.dataIntegrity.signatureOffset == 40)

        port.receiveMode = IxeReceiveMode.widePacketGroup.value | IxeReceiveMode.dataIntegrity.value
        stream.packetGroup.insertSignature = True
        stream.dataIntegrity.insertSignature = True

        port.autoDetectInstrumentation.signature = '{87 73 67 49 42 87 11 80 08 71 00 11}'
        stream.autoDetectInstrumentation.signature = '{87 73 67 49 42 87 11 80 08 71 00 11}'
        port.packetGroup.groupIdOffset = 152
        stream.packetGroup.groupIdOffset = 152
        port.dataIntegrity.signatureOffset = 140
        stream.dataIntegrity.signatureOffset = 140

        port.packetGroup.groupIdMode = 'packetGroupSplit'

        port.write()
        self.ixia.refresh()

        print(json.dumps(port.autoDetectInstrumentation.get_attributes(), indent=4))
        print(json.dumps(port.packetGroup.get_attributes(), indent=4))
        print(json.dumps(port.splitPacketGroup.get_attributes(), indent=4))
        print(json.dumps(port.dataIntegrity.get_attributes(), indent=4))
        print(json.dumps(stream.autoDetectInstrumentation.get_attributes(), indent=4))
        print(json.dumps(stream.packetGroup.get_attributes(), indent=4))
        print(json.dumps(stream.dataIntegrity.get_attributes(), indent=4))

        assert(port.autoDetectInstrumentation.signature == '87 73 67 49 42 87 11 80 08 71 00 11')
        assert(stream.autoDetectInstrumentation.signature == '87 73 67 49 42 87 11 80 08 71 00 11')
        assert(port.packetGroup.groupIdOffset == 152)
        assert(stream.packetGroup.groupIdOffset == 152)
        assert(port.dataIntegrity.signatureOffset == 140)
        assert(stream.dataIntegrity.signatureOffset == 140)

    def test_wrf(self):
        self._reserve_ports(self.port1)

        port = self.ports[self.port1]
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

    #
    # Negative tests.
    #

    def test_errors(self):

        cfg = path.join(path.dirname(__file__), 'configs/good_to_bad_config.prt')
        port = list(self.ixia.session.reserve_ports([self.port1], force=True).values())[0]
        self.ixia.session.login('anotherUser')
        with pytest.raises(TgnError):
            assert(port.reserve())
        self.ixia.session.login(self.config.get('IXE', 'user'))
        port.reserve()
        port.load_config(cfg)
        port.streams[1].framesize = 64
        with pytest.raises(StreamWarningsError):
            assert(port.write())

    def test_negative(self):

        try:
            self.ixia.session.api.call('invalid command')
        except TclError as e:
            print(e)

    def test_port_clear(self):

        self._reserve_ports(self.port1)
        port = self.ports[self.port1]

        stream = port.add_stream()
        stream.protocol.enable802dot1qTag = 1
        stream.vlan.vlanID = 33
        stream.write()
        port.write()

        port.clear()

        port.add_stream()
        port.write()
        # Make sure stream has no VLAN.

    def test_errored_config(self):

        cfg1 = path.join(path.dirname(__file__), 'configs/multi_errors_frame_config.prt')
        self._reserver_and_load(cfg1)
