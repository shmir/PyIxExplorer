import logging
import time
from collections import OrderedDict
from typing import Dict, List, Optional

import trafficgenerator.tgn_tcl
from trafficgenerator import TgnApp, TgnError

from ixexplorer.api.ixapi import FLAG_RDONLY, IxTclHalApi, TclMember, ixe_obj_meta
from ixexplorer.api.tclproto import TclClient
from ixexplorer.ixe_hw import IxeChassis
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_port import IxeCapture, IxeCaptureBuffer, IxePort, IxeReceiveMode
from ixexplorer.ixe_statistics_view import IxeCapFileFormat
from ixexplorer.ixe_stream import IxeStream

logger = logging.getLogger("tgn.ixexplorer")


def init_ixe(host: str, port: Optional[int] = 4555, rsa_id: Optional[str] = None) -> "IxeApp":
    """Connect to Tcl Server and Create IxExplorer object.

    :param host: host (IxTclServer) IP address
    :param port: Tcl Server port
    :param rsa_id: full path to RSA ID file for Linux based IxVM
    """
    return IxeApp(IxTclHalApi(TclClient(logger, host, port, rsa_id)))


class IxeApp(TgnApp):
    def __init__(self, api_wrapper: IxTclHalApi) -> None:
        """Initialize global Tcl interpreter and session."""
        super().__init__(logger, api_wrapper)
        trafficgenerator.tgn_tcl.tcl_interp_g = self.api
        self.session = IxeSession(self.logger, self.api)
        self.chassis_chain: Dict[str, IxeChassis] = {}

    @property
    def connected(self) -> bool:
        """Return whether the port is connected or not."""
        return bool(self.api._tcl_handler.fd)

    def connect(self, user: Optional[str] = None) -> None:
        """Connect to host.

        :param user: if user - login session.
        """
        self.api._tcl_handler.connect()
        if user:
            self.session.login(user)

    def disconnect(self) -> None:
        """Disconnect from all chassis in the chassis chain and logout."""
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
        """Get inventory from all chassis in the chassis chain."""
        for chassis in self.chassis_chain.values():
            chassis.discover()

    def refresh(self) -> None:
        """Refresh (read) configuration from chassis."""
        for chassis in self.chassis_chain.values():
            chassis.refresh()
        self.session._reset_current_object()


class IxeSession(IxeObject, metaclass=ixe_obj_meta):
    """IxTclHal session command."""

    __tcl_command__ = "session"
    __tcl_members__ = [
        TclMember("userName", flags=FLAG_RDONLY),
        TclMember("captureBufferSegmentSize", type=int),
    ]

    __tcl_commands__ = ["login", "logout"]

    def __init__(self, logger_: logging.Logger, api: IxTclHalApi) -> None:
        """Initialize object variables."""
        super().__init__(parent=None, uri="")
        self.logger = logger_
        self.api = api
        IxeObject.session = self

    def add_ports(self, *ports_locations: str) -> Dict[str, IxePort]:
        """Add ports.

        :param ports_locations: list of ports ports_locations <ip, card, port> to reserve
        """
        for port_location in ports_locations:
            chassis_ip, card_num, port_num = port_location.split("/")
            chassis = self.get_objects_with_attribute("chassis", "ipAddress", chassis_ip)[0].id
            uri = f"{chassis} {card_num} {port_num}"
            port = IxePort(parent=self, uri=uri)
            port._data["name"] = port_location
        return self.ports

    def reserve_ports(self, force: bool = False, clear: bool = True) -> None:
        """Reserve ports and reset factory defaults.

        :param force: True - take forcefully, False - fail if port is reserved by other user
        :param clear: True - clear port configuration and statistics, False - leave port as is
        """
        for port in self.ports.values():
            port.reserve(force=force)
            if clear:
                port.clear()
                time.sleep(4)

    def wait_for_up(self, timeout: int = 16, *ports: IxePort) -> None:
        """Wait until ports reach up state.

        :param timeout: seconds to wait.
        :param ports: list of ports to wait for.
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
                call = self.api.call(f"ixCheckLinkState {port}")
                if call == "0":
                    ports_in_up.append(f"{port}")
            ports_in_up = list(set(ports_in_up))
            if len(port_list) == len(ports_in_up):
                return
            time.sleep(1)
        for port in port_list:
            if port not in ports_in_up:
                ports_not_in_up.append(port)
        raise TgnError(f"Ports {ports_not_in_up} not up after {timeout} seconds")

    def clear_all_stats(self, *ports: IxePort) -> None:
        """Clear all statistic counters (port, streams and packet groups) on list of ports.

        :param ports: list of ports to clear.
        """
        port_list = self.set_ports_list(*ports)
        self.api.call_rc(f"ixClearStats {port_list}")
        self.api.call_rc(f"ixClearPacketGroups {port_list}")

    def start_transmit(self, blocking: bool = False, start_packet_groups: bool = True, *ports: IxePort) -> None:
        """Start transmit on ports.

        :param blocking: True - wait for traffic end, False - return after traffic start.
        :param start_packet_groups: True - clear time stamps and start collecting packet groups stats, False - don't.
        :param ports: list of ports to start traffic on, if empty start on all ports.
        """
        port_list = self.set_ports_list(*ports)
        if start_packet_groups:
            port_list_for_packet_groups = self.ports.values()
            port_list_for_packet_groups = self.set_ports_list(*port_list_for_packet_groups)
            self.api.call_rc(f"ixClearTimeStamp {port_list_for_packet_groups}")
            self.api.call_rc(f"ixStartPacketGroups {port_list_for_packet_groups}")
        self.api.call_rc(f"ixStartTransmit {port_list}")
        time.sleep(1)

        if blocking:
            self.wait_transmit(*ports)

    def start_packet_groups(self, clear_time_stamps: bool = True, *ports: IxePort) -> None:
        """Start packet groups on ports.

        :param clear_time_stamps: True - clear time stamps, False - don't.
        :param ports: list of ports to start traffic on, if empty start on all ports.
        """
        port_list = self.set_ports_list(*ports)
        if clear_time_stamps:
            self.api.call_rc(f"ixClearTimeStamp {port_list}")
        self.api.call_rc(f"ixStartPacketGroups {port_list}")

    def stop_transmit(self, *ports: IxePort) -> None:
        """Stop traffic on ports.

        :param ports: list of ports to stop traffic on, if empty start on all ports.
        """
        port_list = self.set_ports_list(*ports)
        self.api.call_rc(f"ixStopTransmit {port_list}")
        time.sleep(0.2)

    def wait_transmit(self, *ports: IxePort) -> None:
        """Wait for traffic end on ports.

        :param ports: list of ports to wait for, if empty wait for all ports.
        """
        port_list = self.set_ports_list(*ports)
        self.api.call_rc(f"ixCheckTransmitDone {port_list}")

    def start_capture(self, *ports: IxePort) -> None:
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
        self.api.call_rc(f"ixStartCapture {port_list}")

    def stop_capture(self, cap_file_name=None, cap_file_format=IxeCapFileFormat.mem, *ports) -> Dict[IxePort, int]:
        """Stop capture on ports.

        :param cap_file_name: prefix for the capture file name.
            Capture files for each port are saved as individual pcap file named 'prefix' + 'URI'.pcap.
        :param cap_file_format: exported file format
        :param ports: list of ports to stop traffic on, if empty stop all ports.
        :return: dictionary (port, packets_per_port)
        """
        port_list = self.set_ports_list(*ports)
        self.api.call_rc(f"ixStopCapture {port_list}")

        packets_per_port = {}
        for port in ports if ports else self.ports.values():
            packets_per_port[port] = port.capture.nPackets
            if packets_per_port[port] and cap_file_format is not IxeCapFileFormat.mem:
                port.cap_file_name = cap_file_name + "-" + port.uri.replace(" ", "_") + "." + cap_file_format.name
                port.captureBuffer.export(port.cap_file_name)
        return packets_per_port

    @staticmethod
    def get_cap_files(*ports: IxePort) -> Dict[IxePort, list]:
        """Return dictionary {port, capture file} of captures files for the requested ports.

        :param ports: list of ports to get capture files names for.
        """
        cap_files = {}
        for port in ports:
            if port.cap_file_name:
                with open(port.cap_file_name) as cap_file:
                    cap_files[port] = cap_file.read().splitlines()
            else:
                cap_files[port] = None
        return cap_files

    def set_ports_list(self, *ports: IxePort) -> str:
        """Set Tcl port list and return the list name to be used by the calling method."""
        if not ports:
            ports = self.ports.values()
        port_uris = [p.uri for p in ports]
        port_list = "pl_" + "_".join(port_uris).replace(" ", "_")
        self.api.call(("set {} [ list " + len(port_uris) * "[list {}] " + "]").format(port_list, *port_uris))
        return port_list

    def set_stream_stats(
        self,
        rx_ports: List[IxePort] = None,
        tx_ports: Dict[IxePort, List[IxeStream]] = None,
        start_offset: int = 40,
        sequence_checking: bool = True,
        data_integrity: bool = True,
        timestamp: bool = True,
    ) -> None:
        """Set TX ports and RX streams for stream statistics.

        :param rx_ports: list of ports to set RX pgs. If empty set for all ports.
        :param tx_ports: list of streams to set TX pgs. If empty set for all streams.
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

    def set_prbs(self, rx_ports: List[IxePort] = None, tx_ports: Dict[IxePort, List[IxeStream]] = None) -> None:
        """Set TX ports and RX streams for stream statistics.

        :param rx_ports: list of ports to set RX PRBS. If empty set for all ports.
        :param tx_ports: list of streams to set TX PRBS. If empty set for all streams.
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
