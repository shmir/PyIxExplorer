
import logging

from ixexplorer.api.tclproto import TclClient
from ixexplorer.api.ixapi import IxTclHalApi

from trafficgenerator.trafficgenerator import TrafficGenerator
from ixexplorer.ixe_object import IxeObject
from ixexplorer.pyixia import Session, Chassis

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
