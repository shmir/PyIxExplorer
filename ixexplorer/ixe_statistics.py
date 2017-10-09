
from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY
from ixexplorer.ixe_object import IxeObject


class IxePortStatistics(IxeObject):
    """Per port statistics."""

    __tcl_command__ = 'stat'
    __tcl_members__ = [
            TclMember('bitsReceived', type=int, flags=FLAG_RDONLY),
            TclMember('bitsSent', type=int, flags=FLAG_RDONLY),
            TclMember('bytesReceived', type=int, flags=FLAG_RDONLY),
            TclMember('bytesSent', type=int, flags=FLAG_RDONLY),
    ]

    def __init__(self, parent):
        super(self.__class__, self).__init__(uri=parent.uri, parent=parent)

    def _ix_get(self, member):
        self.api.call('stat get {} {}'.format(member.name, self.uri))

    def _ix_set(self, member):
        self.api.call('stat set {} {}'.format(member.name, self.uri))
