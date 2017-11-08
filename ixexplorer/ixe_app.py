
import time

from trafficgenerator.tgn_utils import ApiType, TgnError
from trafficgenerator.tgn_app import TgnApp

from ixexplorer.api.tclproto import TclClient
from ixexplorer.api.ixapi import IxTclHalApi, TclMember, FLAG_RDONLY
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_hw import IxeChassis, IxePort
from ixexplorer.ixe_statistics_view import IxeCapture, IxeCaptureBuffer, IxeCapFileFormat


def init_ixe(api, logger, host, port=4555, rsa_id=None):
    """ Create STC object.

    :param api: socket/tcl
    :type api: trafficgenerator.tgn_utils.ApiType
    :param logger: python logger object
    :param host: chassis IP address
    :param port: Tcl server port
    :param rsa_id: full path to RSA ID file for Linux based IxVM
    :return: IXE object
    """

    if api == ApiType.tcl:
        raise TgnError('Tcl API not supported in this version.')

    return IxeApp(logger, IxTclHalApi(TclClient(logger, host, port, rsa_id)))


class IxeApp(TgnApp):
    """ This version supports only one chassis. """

    def __init__(self, logger, api_wrapper):
        super(self.__class__, self).__init__(logger, api_wrapper)
        IxeObject.api = self.api
        IxeObject.logger = logger
        self.session = IxeSession()
        IxeObject.session = self.session

    def connect(self, chassis):
        self.chassis = IxeChassis(chassis)
        self.api._tcl_handler.connect()
        self.chassis.connect()

    def disconnect(self):
        self.chassis.disconnect()
        self.api._tcl_handler.close()

    def discover(self):
        return self.chassis.discover()

    def refresh(self):
        self.chassis.refresh()
        self.session._reset_current_object()


class IxeSession(IxeObject):
    __tcl_command__ = 'session'
    __tcl_members__ = [
            TclMember('userName', flags=FLAG_RDONLY),
            TclMember('captureBufferSegmentSize', type=int),
    ]

    __tcl_commands__ = ['login', 'logout']

    port_lists = []

    def __init__(self):
        super(self.__class__, self).__init__(uri='', parent=None)

    def reserve_ports(self, ports_uri, force=False, clear=True):
        """ Reserve ports and reset factory defaults.

        :param force: True - take forcefully, False - fail if port is reserved by other user
        :param clear: True - clear port configuration and statistics, False - leave port as is
        :param ports_uri: list of ports uris to reserve
        :return: ports dictionary (port uri, port object)
        """

        for port_uri in ports_uri:
            port = IxePort(parent=self, uri=port_uri)
            port.reserve(force=force)
            if clear:
                port.ix_set_default()
                port.setFactoryDefaults()
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
            self.wait_transmit(ports)

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

        port_list = self.set_ports_list(*ports)
        self.api.call_rc('ixStartCapture {}'.format(port_list))

    def stop_capture(self, cap_file_name, cap_file_format=IxeCapFileFormat.enc, *ports):
        """ Stop capture on ports.

        :param cap_file_name: prefix for the capture file name.
            Capture files for each port are saved as individual pcap file named 'prefix' + 'URI'.pcap.
        :param cap_file_format: exported file format
        :param ports: list of ports to stop traffic on, if empty stop all ports.
        :return: dictionary (port, full path of pcap file name)
        """

        port_list = self.set_ports_list(*ports)
        self.api.call_rc('ixStopCapture {}'.format(port_list))

        cap_file_names = {}
        for port in (ports if ports else self.ports.values()):
            port_cap = IxeCapture(parent=port)
            num_frames = port_cap.nPackets
            if num_frames:
                cap_file_names[port] = cap_file_name + '-' + port.uri.replace(' ', '_') + '.' + cap_file_format.name
                port_buffer = IxeCaptureBuffer(parent=port, num_frames=num_frames)
                port_buffer.ix_get(force=True)
                port_buffer.export(cap_file_names[port])
        return cap_file_names

    def set_ports_list(self, *ports):
        if not ports:
            ports = self.ports.values()
        port_uris = [p.uri for p in ports]
        port_list = 'pl_' + '_'.join(port_uris).replace(' ', '_')
        if port_list not in self.port_lists:
            self.api.call(('set {} [ list ' + len(port_uris) * '[list {}] ' + ']').format(port_list, *port_uris))
        return port_list
