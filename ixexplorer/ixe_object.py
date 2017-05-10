
from trafficgenerator.tgn_object import TgnObject

from ixexplorer.api.ixapi import _MetaIxTclApi, TclMember, FLAG_RDONLY


attributes_xml = ''


class IxeObject(TgnObject):

    __metaclass__ = _MetaIxTclApi

    def __init__(self, **data):
        pass

    def _create(self):
        pass


class IxeStream(IxeObject):

    def __init__(self, **data):
        pass


class Statistics(object):
    """Per port statistics."""
    __metaclass__ = _MetaIxTclApi
    __tcl_command__ = 'stat'
    __tcl_members__ = [
            TclMember('bytesReceived', type=int, flags=FLAG_RDONLY),
    ]

    def __init__(self, api, port):
        self._api = api
        self.port = port

    def _ix_get(self, member):
        self._api.call('stat get %s %d %d %d', member.name, *self.port._port_id())

    def _ix_set(self, member):
        self._api.call('stat set %s %d %d %d', member.name, *self.port._port_id())
