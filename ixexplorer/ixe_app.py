
import logging

from pyixia.tclproto import TclClient
from pyixia.ixapi import _MetaIxTclApi, TclMember, FLAG_RDONLY
from pyixia.ixapi import IxTclHalApi

from trafficgenerator.trafficgenerator import TrafficGenerator
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_hw import Chassis

log = logging.getLogger(__name__)


class IxeApp(TrafficGenerator):
    """This class supports only one chassis atm."""
    def __init__(self, logger, host, port=4555, rsa_id=None):
        self.host = host
        self._tcl = TclClient(host, port, rsa_id)
        self.api = IxTclHalApi(self._tcl)
        IxeObject.api = self.api
        IxeObject._api = self.api
        self.chassis = Chassis(host)
        self.session = Session()
        IxeObject.api = self.api
        IxeObject.logger = logger

    def connect(self):
        self._tcl.connect()
        self.chassis.connect()

    def disconnect(self):
        self.chassis.disconnect()
        self._tcl.close()

    def discover(self):
        return self.chassis.discover()


class Session(IxeObject):
    __metaclass__ = _MetaIxTclApi
    __tcl_command__ = 'session'
    __tcl_members__ = [
            TclMember('userName', flags=FLAG_RDONLY),
            TclMember('captureBufferSegmentSize', type=int),
    ]

    def _ix_get(self, member):
        self._api.call_rc('session get')

    def _ix_set(self, member):
        self._api.call_rc('session set')

    def login(self, username):
        self._api.call_rc('session login %s', username)

    def logout(self):
        self._api.call_rc('session logout')


class PortGroup(object):
    START_TRANSMIT = 7
    STOP_TRANSMIT = 8
    START_CAPTURE = 9
    STOP_CAPTURE = 10
    RESET_STATISTICS = 13
    PAUSE_TRANSMIT = 15
    STEP_TRANSMIT = 16
    TRANSMIT_PING = 17
    TAKE_OWNERSHIP = 40
    TAKE_OWNERSHIP_FORCED = 41
    CLEAR_OWNERSHIP = 42
    CLEAR_OWNERSHIP_FORCED = 43

    __metaclass__ = _MetaIxTclApi
    __tcl_command__ = 'portGroup'
    __tcl_members__ = [
            TclMember('lastTimeStamp', type=int, flags=FLAG_RDONLY),
    ]

    next_free_id = 1

    def __init__(self, api, id=None):
        self._api = api
        if id is None:
            self.id = self.next_free_id
            self.next_free_id += 1
        else:
            self.id = id

    def _ix_get(self):
        pass

    def create(self):
        self._api.call_rc('portGroup create %s', self.id)

    def destroy(self):
        self._api.call_rc('portGroup destroy %s', self.id)

    def add_port(self, port):
        self._api.call_rc('portGroup add %s %d %d %d', self.id, *port._port_id())

    def del_port(self, port):
        self._api.call_rc('portGroup del %s %d %d %d', self.id, *port._port_id())

    def _set_command(self, cmd):
        self._api.call_rc('portGroup setCommand %s %d', self.id, cmd)

    def start_transmit(self):
        self._set_command(self.START_TRANSMIT)

    def stop_transmit(self):
        self._set_command(self.STOP_TRANSMIT)

    def start_capture(self):
        self._set_command(self.START_CAPTURE)

    def stop_capture(self):
        self._set_command(self.STOP_CAPTURE)

    def reset_statistics(self):
        self._set_command(self.RESET_STATISTICS)

    def pause_transmit(self):
        self._set_command(self.PAUSE_TRANSMIT)

    def step_transmit(self):
        self._set_command(self.STEP_TRANSMIT)

    def transmit_ping(self):
        self._set_command(self.TRANSMIT_PING)

    def take_ownership(self, force=False):
        if not force:
            self._set_command(self.TAKE_OWNERSHIP)
        else:
            self._set_command(self.TAKE_OWNERSHIP_FORCED)

    def clear_ownership(self, force=False):
        if not force:
            self._set_command(self.CLEAR_OWNERSHIP)
        else:
            self._set_command(self.CLEAR_OWNERSHIP_FORCED)
