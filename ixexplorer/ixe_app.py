import logging
import time
from collections import OrderedDict
from typing import Dict, Optional

import trafficgenerator.tgn_tcl
from trafficgenerator import TgnApp, TgnError

from ixexplorer.api.ixapi import FLAG_RDONLY, IxTclHalApi, TclMember, ixe_obj_meta
from ixexplorer.api.tclproto import TclClient
from ixexplorer.ixe_hw import IxeChassis
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_port import IxeCapture, IxeCaptureBuffer, IxePhyMode, IxePort, IxeReceiveMode
from ixexplorer.ixe_statistics_view import IxeCapFileFormat

logger = logging.getLogger("tgn.ixexplorer")


def init_ixe(host: str, port: Optional[int] = 4555, rsa_id: Optional[str] = None) -> "IxeApp":
    """Connect to Tcl Server and Create IxExplorer object.

    :param host: host (IxTclServer) IP address
    :param port: Tcl Server port
    :param rsa_id: full path to RSA ID file for Linux based IxVM
    """
    return IxeApp(IxTclHalApi(TclClient(logger, host, port, rsa_id)))


class IxeApp(TgnApp):
    def __init__(self, api_wrapper: IxTclHalApi):
        super().__init__(logger, api_wrapper)
        trafficgenerator.tgn_tcl.tcl_interp_g = self.api
        self.session = IxeSession(self.logger, self.api)
        self.chassis_chain = {}

    @property
    def connected(self):
        return True if self.api._tcl_handler.fd else False

    def connect(self, user=None):
        """Connect to host.

        :param user: if user - login session.
        """
        self.api._tcl_handler.connect()
        if user:
            self.session.login(user)

    def disconnect(self) -> None:
        for chassis in self.chassis_chain.values():
            chassis.disconnect()
        self.session.logout()
        self.api._tcl_handler.close()

    def add(self, chassis: str) -> None:
        """Add chassis.

        :param chassis: chassis IP address.
        """
        if chassis not in self.chassis_chain:
            self.chassis_chain[chassis] = IxeChassis(self.session, chassis)
            self.chassis_chain[chassis].connect()

    def discover(self) -> None:
        for chassis in self.chassis_chain.values():
            chassis.discover()

    def refresh(self) -> None:
        for chassis in self.chassis_chain.values():
            chassis.refresh()
        self.session._reset_current_object()


class IxeSession(IxeObject, metaclass=ixe_obj_meta):
    __tcl_command__ = "session"
    __tcl_members__ = [
        TclMember("userName", flags=FLAG_RDONLY),
        TclMember("captureBufferSegmentSize", type=int),
    ]

    __tcl_commands__ = ["login", "logout"]

    port_lists = []

    def __init__(self, logger, api):
        super().__init__(parent=None, uri="")
        self.logger = logger
        self.api = api
        IxeObject.session = self

    def reserve_ports(self, force=False, clear=True) -> None:
        """Reserve ports and reset factory defaults.

        :param force: True - take forcefully, False - fail if port is reserved by other user
        :param clear: True - clear port configuration and statistics, False - leave port as is
        """
        for port in self.ports.values():
            port.reserve(force=force)
            if clear:
                port.clear()
                time.sleep(4)

    def add_ports(self, *ports_locations: str) -> Dict[str, IxePort]:
        """Add ports.

        :param ports_locations: list of ports ports_locations <ip, card, port> to reserve
        """
        for port_location in ports_locations:
            ip, card, port = port_location.split("/")
            chassis = self.get_objects_with_attribute("chassis", "ipAddress", ip)[0].id
            uri = f"{chassis} {card} {port}"
            port = IxePort(parent=self, uri=uri)
            port._data["name"] = port_location
        return self.ports

    def wait_for_up(self, timeout=16, ports=None):
        """Wait until ports reach up state.

        :param timeout: seconds to wait.
        :param ports: list of ports to wait for.
        :return:
        """
        port_list = []
        for port in ports:
            port_list.append(self.set_ports_list(port))
        t_end = time.time() + timeout
        ports_not_in_up = []
        ports_in_up = []
        while time.time() < t_end:
            # ixCheckLinkState can take few seconds on some ports when link is down.
            for port in port_list:
                call = self.api.call("ixCheckLinkState {}".format(port))
                if call == "0":
                    ports_in_up.append("{}".format(port))
                else:
                    pass
            ports_in_up = list(set(ports_in_up))
            if len(port_list) == len(ports_in_up):
                return
            time.sleep(1)
        for port in port_list:
            if port not in ports_in_up:
                ports_not_in_up.append(port)
        raise TgnError("{}".format(ports_not_in_up))

    def clear_all_stats(self, *ports):
        """Clear all statistic counters (port, streams and packet groups) on list of ports.

        :param ports: list of ports to clear.
        """

        port_list = self.set_ports_list(*ports)
        self.api.call_rc("ixClearStats {}".format(port_list))
        self.api.call_rc("ixClearPacketGroups {}".format(port_list))

    def start_transmit(self, blocking=False, start_packet_groups=True, *ports):
        """Start transmit on ports.

        :param blocking: True - wait for traffic end, False - return after traffic start.
        :param start_packet_groups: True - clear time stamps and start collecting packet groups stats, False - don't.
        :param ports: list of ports to start traffic on, if empty start on all ports.
        """

        port_list = self.set_ports_list(*ports)
        if start_packet_groups:
            port_list_for_packet_groups = self.ports.values()
            port_list_for_packet_groups = self.set_ports_list(*port_list_for_packet_groups)
            self.api.call_rc("ixClearTimeStamp {}".format(port_list_for_packet_groups))
            self.api.call_rc("ixStartPacketGroups {}".format(port_list_for_packet_groups))
        self.api.call_rc("ixStartTransmit {}".format(port_list))
        time.sleep(1)

        if blocking:
            self.wait_transmit(*ports)

    def start_packet_groups(self, clear_time_stamps=True, *ports):
        """Start packet groups on ports.

        :param clear_time_stamps: True - clear time stamps, False - don't.
        :param ports: list of ports to start traffic on, if empty start on all ports.
        """
        port_list = self.set_ports_list(*ports)
        if clear_time_stamps:
            self.api.call_rc("ixClearTimeStamp {}".format(port_list))
        self.api.call_rc("ixStartPacketGroups {}".format(port_list))

    def stop_transmit(self, *ports):
        """Stop traffic on ports.

        :param ports: list of ports to stop traffic on, if empty start on all ports.
        """

        port_list = self.set_ports_list(*ports)
        self.api.call_rc("ixStopTransmit {}".format(port_list))
        time.sleep(0.2)

    def wait_transmit(self, *ports):
        """Wait for traffic end on ports.

        :param ports: list of ports to wait for, if empty wait for all ports.
        """

        port_list = self.set_ports_list(*ports)
        self.api.call_rc("ixCheckTransmitDone {}".format(port_list))

    def start_capture(self, *ports):
        """Start capture on ports.

        :param ports: list of ports to start capture on, if empty start on all ports.
        """

        IxeCapture.current_object = None
        IxeCaptureBuffer.current_object = None
        if not ports:
            ports = self.ports.values()
        for port in ports:
            port.captureBuffer = None
        port_list = self.set_ports_list(*ports)
        self.api.call_rc("ixStartCapture {}".format(port_list))

    def stop_capture(self, cap_file_name=None, cap_file_format=IxeCapFileFormat.mem, *ports):
        """Stop capture on ports.

        :param cap_file_name: prefix for the capture file name.
            Capture files for each port are saved as individual pcap file named 'prefix' + 'URI'.pcap.
        :param cap_file_format: exported file format
        :param ports: list of ports to stop traffic on, if empty stop all ports.
        :return: dictionary (port, nPackets)
        """
        port_list = self.set_ports_list(*ports)
        self.api.call_rc("ixStopCapture {}".format(port_list))

        nPackets = {}
        for port in ports if ports else self.ports.values():
            nPackets[port] = port.capture.nPackets
            if nPackets[port]:
                if cap_file_format is not IxeCapFileFormat.mem:
                    port.cap_file_name = cap_file_name + "-" + port.uri.replace(" ", "_") + "." + cap_file_format.name
                    port.captureBuffer.export(port.cap_file_name)
        return nPackets

    def get_cap_files(self, *ports):
        """
        :param ports: list of ports to get capture files names for.
        :return: dictionary (port, capture file)
        """
        cap_files = {}
        for port in ports:
            if port.cap_file_name:
                with open(port.cap_file_name) as f:
                    cap_files[port] = f.read().splitlines()
            else:
                cap_files[port] = None
        return cap_files

    def set_ports_list(self, *ports):
        if not ports:
            ports = self.ports.values()
        port_uris = [p.uri for p in ports]
        port_list = "pl_" + "_".join(port_uris).replace(" ", "_")
        if port_list not in self.port_lists:
            self.api.call(("set {} [ list " + len(port_uris) * "[list {}] " + "]").format(port_list, *port_uris))
        return port_list

    def set_stream_stats(
        self, rx_ports=None, tx_ports=None, start_offset=40, sequence_checking=True, data_integrity=True, timestamp=True
    ):
        """Set TX ports and RX streams for stream statistics.

        :param ports: list of ports to set RX pgs. If empty set for all ports.
        :type ports: list[ixexplorer.ixe_port.IxePort]
        :param tx_ports: list of streams to set TX pgs. If empty set for all streams.
        :type tx_ports:  dict[ixexplorer.ixe_port.IxePort, list[ixexplorer.ixe_stream.IxeStream]]
        :param sequence_checking: True - enable sequence checkbox, False - disable
        :param data_integrity: True - enable data integrity checkbox, False - disable
        :param timestamp: True - enable timestamp checkbox, False - disable
        :param start_offset: start offset for signatures (group ID, signature, sequence)
        """

        if not rx_ports:
            rx_ports = self.ports.values()

        if not tx_ports:
            tx_ports = {}
            for port in self.ports.values():
                tx_ports[port] = port.streams.values()

        groupIdOffset = start_offset
        signatureOffset = start_offset + 4
        next_offset = start_offset + 8
        if sequence_checking:
            sequenceNumberOffset = next_offset
            next_offset += 4
        if data_integrity:
            di_signatureOffset = next_offset

        for port in rx_ports:
            modes = []
            modes.append(IxeReceiveMode.widePacketGroup)
            port.packetGroup.groupIdOffset = groupIdOffset
            port.packetGroup.signatureOffset = signatureOffset
            if sequence_checking and int(port.isValidFeature("portFeatureRxSequenceChecking")):
                modes.append(IxeReceiveMode.sequenceChecking)
                port.packetGroup.sequenceNumberOffset = sequenceNumberOffset
            if data_integrity and int(port.isValidFeature("portFeatureRxDataIntegrity")):
                modes.append(IxeReceiveMode.dataIntegrity)
                port.dataIntegrity.signatureOffset = di_signatureOffset
            if timestamp and int(port.isValidFeature("portFeatureRxFirstTimeStamp")):
                port.dataIntegrity.enableTimeStamp = True
            else:
                port.dataIntegrity.enableTimeStamp = False
            port.set_receive_modes(*modes)

            port.write()

        for port, streams in tx_ports.items():
            for stream in streams:
                stream.packetGroup.insertSignature = True
                stream.packetGroup.groupIdOffset = groupIdOffset
                stream.packetGroup.signatureOffset = signatureOffset
                if sequence_checking:
                    stream.packetGroup.insertSequenceSignature = True
                    stream.packetGroup.sequenceNumberOffset = sequenceNumberOffset
                if data_integrity and int(port.isValidFeature("portFeatureRxDataIntegrity")):
                    stream.dataIntegrity.insertSignature = True
                    stream.dataIntegrity.signatureOffset = di_signatureOffset
                if timestamp:
                    stream.enableTimestamp = True
                else:
                    stream.enableTimestamp = False

            port.write()

    def set_prbs(self, rx_ports=None, tx_ports=None):
        """Set TX ports and RX streams for stream statistics.

        :param ports: list of ports to set RX PRBS. If empty set for all ports.
        :type ports: list[ixexplorer.ixe_port.IxePort]
        :param tx_ports: list of streams to set TX PRBS. If empty set for all streams.
        :type tx_ports:  dict[ixexplorer.ixe_port.IxePort, list[ixexplorer.ixe_stream.IxeStream]]
        """

        if not rx_ports:
            rx_ports = self.ports.values()

        if not tx_ports:
            tx_ports = {}
            for port in self.ports.values():
                tx_ports[port] = port.streams.values()

        for port in rx_ports:
            port.set_receive_modes(IxeReceiveMode.widePacketGroup, IxeReceiveMode.sequenceChecking, IxeReceiveMode.prbs)
            port.enableAutoDetectInstrumentation = True
            port.autoDetectInstrumentation.ix_set_default()
            port.write()

        for port, streams in tx_ports.items():
            for stream in streams:
                stream.autoDetectInstrumentation.enableTxAutomaticInstrumentation = True
                stream.autoDetectInstrumentation.enablePRBS = True
            port.write()

    #
    # Properties.
    #

    def get_ports(self) -> Dict[str, IxePort]:
        """Get dictionary {name: object} of all reserved ports."""
        return OrderedDict({str(p): p for p in self.get_objects_by_type("port")})

    ports = property(get_ports)
