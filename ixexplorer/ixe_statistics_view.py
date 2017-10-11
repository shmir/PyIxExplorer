"""
Classes and utilities to manage IxExplorer statistics views.
"""

from collections import OrderedDict

from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY
from ixexplorer.ixe_object import IxeObject


class IxeStat(IxeObject):
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
            TclMember('duplexMode', type=int, flags=FLAG_RDONLY),
            TclMember('link', type=int, flags=FLAG_RDONLY),
            TclMember('lineSpeed', type=int, flags=FLAG_RDONLY),
            TclMember('duplexMode', type=int, flags=FLAG_RDONLY),
    ]

    def __init__(self, parent):
        super(IxeStat, self).__init__(uri=parent.uri, parent=parent)


class IxeStatTotal(IxeStat):
    __get_command__ = 'get statAllStats'


class IxeStatRate(IxeStat):
    __get_command__ = 'getRate statAllStats'


class IxePgStats(IxeObject):
    __tcl_command__ = 'packetGroupStats'
    __tcl_members__ = [
            TclMember('totalFrames', type=int, flags=FLAG_RDONLY),
            TclMember('frameRate', type=int, flags=FLAG_RDONLY),
            TclMember('totalByteCount', type=int, flags=FLAG_RDONLY),
            TclMember('byteRate', type=int, flags=FLAG_RDONLY),
            TclMember('bitRate', type=int, flags=FLAG_RDONLY),
            TclMember('minLatency', type=int, flags=FLAG_RDONLY),
            TclMember('maxLatency', type=int, flags=FLAG_RDONLY),
            TclMember('averageLatency', type=int, flags=FLAG_RDONLY),
    ]

    def __init__(self, parent):
        super(self.__class__, self).__init__(uri=parent.uri + ' ' + parent.uri[-1], parent=parent)


class IxeStats(object):
    pass


class IxePortsStats(IxeStats):

    def read_stats(self):
        self.statistics = OrderedDict()
        session = IxeObject.session
        for port_name, port in session.ports.items():
            port_stats = IxeStatTotal(port).get_attributes(FLAG_RDONLY)
            port_stats.update({c + '_rate': v for c, v in IxeStatRate(port).get_attributes(FLAG_RDONLY).items()})
            self.statistics[port_name] = port_stats


class IxeStreamsStats(IxeStats):

    def read_stats(self):
        self.statistics = OrderedDict()
        session = IxeObject.session
        for port in session.ports.values():
            for stream_name, stream in port.streams.items():
                self.statistics[stream_name] = IxePgStats(stream).get_attributes(FLAG_RDONLY)
