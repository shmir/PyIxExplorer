
import time

from trafficgenerator.tgn_app import TgnApp

from ixexplorer.api.tclproto import TclClient
from ixexplorer.api.ixapi import IxTclHalApi, TclMember, FLAG_RDONLY
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_hw import IxeChassis
from ixexplorer.ixe_port import IxePort, IxePhyMode, IxeCapture, IxeCaptureBuffer, IxeReceiveMode
from ixexplorer.ixe_statistics_view import IxeCapFileFormat


def init_ixe(api, logger, host, port=4555, rsa_id=None):
    """ Connect to Tcl Server and Create IxExplorer object.

    :param api: socket/tcl - tcl not supported in this version.
    :type api: trafficgenerator.tgn_utils.ApiType
    :param logger: python logger object
    :param host: host (IxTclServer) IP address
    :param port: Tcl Server port
    :param rsa_id: full path to RSA ID file for Linux based IxVM
    :return: IXE object
    """

    return IxeApp(logger, IxTclHalApi(TclClient(logger, host, port, rsa_id)))


class IxeApp(TgnApp):

    def __init__(self, logger, api_wrapper):
        super(self.__class__, self).__init__(logger, api_wrapper)
        self.session = IxeSession(self.logger, self.api)
        self.chassis_chain = {}

    def connect(self, user=None):
        """ Connect to host.

        :param user: if user - login session.
        """

        self.api._tcl_handler.connect()
        if user:
            self.session.login(user)

    def disconnect(self):
        for chassis in self.chassis_chain.values():
            chassis.disconnect()
        self.session.logout()
        self.api._tcl_handler.close()

    def add(self, chassis):
        """ add chassis.

        :param chassis: chassis IP address.
        """

        self.chassis_chain[chassis] = IxeChassis(self.session, chassis, len(self.chassis_chain) + 1)
        self.chassis_chain[chassis].connect()

    def discover(self):
        for chassis in self.chassis_chain.values():
            chassis.discover()

    def refresh(self):
        for chassis in self.chassis_chain.values():
            chassis.refresh()
        self.session._reset_current_object()


class IxeSession(IxeObject):
    __tcl_command__ = 'session'
    __tcl_members__ = [
            TclMember('userName', flags=FLAG_RDONLY),
            TclMember('captureBufferSegmentSize', type=int),
    ]

    __tcl_commands__ = ['login', 'logout']

    port_lists = []

    def __init__(self, logger, api):
        super(self.__class__, self).__init__(uri='', parent=None)
        self.logger = logger
        self.api = api
        self.session = self

    def reserve_ports(self, ports_locations, force=False, clear=True, phy_mode=IxePhyMode.ignore):
        """ Reserve ports and reset factory defaults.

        :param ports_locations: list of ports ports_locations <ip, card, port> to reserve
        :param force: True - take forcefully, False - fail if port is reserved by other user
        :param clear: True - clear port configuration and statistics, False - leave port as is
        :param phy_mode: requested PHY mode.
        :return: ports dictionary (port uri, port object)
        """

        for port_location in ports_locations:
            ip, card, port = port_location.split('/')
            chassis = self.get_objects_with_attribute('chassis', 'ipAddress', ip)[0].id
            uri = '{} {} {}'.format(chassis, card, port)
            port = IxePort(parent=self, uri=uri)
            port._data['name'] = port_location
            port.reserve(force=force)
            if clear:
                port.ix_set_default()
                port.setFactoryDefaults()
                port.set_phy_mode(phy_mode)
                port.reset()
                port.write()
                port.clear_stats()

        return self.ports

    def get_ports(self):
        """
        :return: dictionary {name: object} of all reserved ports.
        """

        return {str(p): p for p in self.get_objects_by_type('port')}
    ports = property(get_ports)

    def start_transmit(self, blocking=False, *ports):
        """ Start transmit on ports.

        :param blocking: True - wait for traffic end, False - return after traffic start.
        :param ports: list of ports to start traffic on, if empty start on all ports.
        """

        port_list = self.set_ports_list(*ports)
        self.api.call_rc('ixClearTimeStamp {}'.format(port_list))
        self.api.call_rc('ixStartPacketGroups {}'.format(port_list))
        self.api.call_rc('ixStartTransmit {}'.format(port_list))
        time.sleep(2)
        if blocking:
            self.wait_transmit(*ports)

    def stop_transmit(self, *ports):
        """ Stop traffic on ports.

        :param ports: list of ports to stop traffic on, if empty start on all ports.
        """

        port_list = self.set_ports_list(*ports)
        self.api.call_rc('ixStopTransmit {}'.format(port_list))
        time.sleep(2)

    def wait_transmit(self, *ports):
        """ Wait for traffic end on ports.

        :param ports: list of ports to wait for, if empty wait for all ports.
        """

        port_list = self.set_ports_list(*ports)
        self.api.call_rc('ixCheckTransmitDone {}'.format(port_list))

    def start_capture(self, *ports):
        """ Start capture on ports.

        :param ports: list of ports to start capture on, if empty start on all ports.
        """

        IxeCapture.current_object = None
        IxeCaptureBuffer.current_object = None
        if not ports:
            ports = self.ports.values()
        for port in ports:
            port.captureBuffer = None
        port_list = self.set_ports_list(*ports)
        self.api.call_rc('ixStartCapture {}'.format(port_list))

    def stop_capture(self, cap_file_name=None, cap_file_format=IxeCapFileFormat.mem, *ports):
        """ Stop capture on ports.

        :param cap_file_name: prefix for the capture file name.
            Capture files for each port are saved as individual pcap file named 'prefix' + 'URI'.pcap.
        :param cap_file_format: exported file format
        :param ports: list of ports to stop traffic on, if empty stop all ports.
        :return: dictionary (port, nPackets)
        """

        port_list = self.set_ports_list(*ports)
        self.api.call_rc('ixStopCapture {}'.format(port_list))

        nPackets = {}
        for port in (ports if ports else self.ports.values()):
            nPackets[port] = port.capture.nPackets
            if nPackets[port]:
                if cap_file_format is not IxeCapFileFormat.mem:
                    port.cap_file_name = cap_file_name + '-' + port.uri.replace(' ', '_') + '.' + cap_file_format.name
                    port.captureBuffer.export(port.cap_file_name)
        return nPackets

    def get_cap_files(self, *ports):
        """
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
        port_list = 'pl_' + '_'.join(port_uris).replace(' ', '_')
        if port_list not in self.port_lists:
            self.api.call(('set {} [ list ' + len(port_uris) * '[list {}] ' + ']').format(port_list, *port_uris))
        return port_list

    def set_stream_stats(self, rx_ports=None, tx_ports=None, start_offset=40):
        """ Set TX ports and RX streams for stream statistics.

        :param ports: list of ports to set RX pgs. If empty set for all ports.
        :type ports: list[ixexplorer.ixe_port.IxePort]
        :param tx_ports: list of streams to set TX pgs. If empty set for all streams.
        :type tx_ports:  dict[ixexplorer.ixe_port.IxePort, list[ixexplorer.ixe_stream.IxeStream]]
        :param start_offset: start offset for signatures (group ID, signature, sequence)
        """

        if not rx_ports:
            rx_ports = self.ports.values()

        if not tx_ports:
            tx_ports = {}
            for port in self.ports.values():
                tx_ports[port] = port.streams.values()

        for port in rx_ports:
            modes = []
            if int(port.isValidFeature('portFeatureRxWidePacketGroups')):
                modes.append(IxeReceiveMode.widePacketGroup)
                port.packetGroup.groupIdOffset = start_offset
                port.packetGroup.signatureOffset = start_offset + 4
            if int(port.isValidFeature('portFeatureRxSequenceChecking')):
                modes.append(IxeReceiveMode.sequenceChecking)
                port.packetGroup.sequenceNumberOffset = start_offset + 8
            if int(port.isValidFeature('portFeatureRxDataIntegrity')):
                modes.append(IxeReceiveMode.dataIntegrity)
                port.dataIntegrity.signatureOffset = start_offset + 12
            port.set_receive_modes(*modes)

            port.write()

        for port, streams in tx_ports.items():
            for stream in streams:

                stream.packetGroup.insertSignature = True
                stream.packetGroup.insertSequenceSignature = True
                stream.dataIntegrity.insertSignature = True

                stream.packetGroup.groupIdOffset = start_offset
                stream.packetGroup.signatureOffset = start_offset + 4
                stream.packetGroup.sequenceNumberOffset = start_offset + 8
                stream.dataIntegrity.signatureOffset = start_offset + 12

            port.write()
