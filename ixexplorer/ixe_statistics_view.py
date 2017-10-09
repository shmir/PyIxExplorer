"""
Classes and utilities to manage IxExplorer statistics views.
"""

from collections import OrderedDict

from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY
from ixexplorer.ixe_object import IxeObject


class IxePortStats(IxeObject):
    __tcl_command__ = 'stat'
    __tcl_members__ = [
            TclMember('framesSent', type=int, flags=FLAG_RDONLY),
            TclMember('framesReceived', type=int, flags=FLAG_RDONLY),
            TclMember('bytesSent', type=int, flags=FLAG_RDONLY),
            TclMember('bytesReceived', type=int, flags=FLAG_RDONLY),
            TclMember('bitsReceived', type=int, flags=FLAG_RDONLY),
            TclMember('captureTrigger', type=int, flags=FLAG_RDONLY),
            TclMember('captureFilter', type=int, flags=FLAG_RDONLY),
            TclMember('userDefinedStat1', type=int, flags=FLAG_RDONLY),
            TclMember('userDefinedStat2', type=int, flags=FLAG_RDONLY),
            TclMember('vlanTaggedFramesRx', type=int, flags=FLAG_RDONLY),
            TclMember('ipPackets', type=int, flags=FLAG_RDONLY),
            TclMember('udpPackets', type=int, flags=FLAG_RDONLY),
            TclMember('transmitDuration', type=int, flags=FLAG_RDONLY),
            TclMember('link', type=int, flags=FLAG_RDONLY),
            TclMember('lineSpeed', type=int, flags=FLAG_RDONLY),
            TclMember('duplexMode', type=int, flags=FLAG_RDONLY),
    ]

    def __init__(self):
        super(self.__class__, self).__init__(uri=' ', parent=IxeObject.session)

    def _ix_get(self, member=None):
        pass

    def read_stats(self):
        session = IxeObject.session
        self.statistics = OrderedDict()
        for port_name, port in session.ports.items():
            port_stats = OrderedDict()
            self.api.call_rc('stat get statAllStats {}'.format(port.uri))
            for member in IxePortStats.__tcl_members__:
                if member.flags & FLAG_RDONLY:
                    port_stats[member.attrname] = getattr(self, member.attrname)
            self.api.call_rc('stat getRate statAllStats {}'.format(port.uri))
            for member in IxePortStats.__tcl_members__:
                if member.flags & FLAG_RDONLY:
                    port_stats[member.attrname + '_rate'] = getattr(self, member.attrname)
            self.statistics[port_name] = port_stats
