"""
Classes and utilities to manage IxExplorer statistics views.
"""

import time
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


class IxeStreamTxStats(IxeObject):
    __tcl_command__ = 'streamTransmitStats'
    __get_command__ = 'getGroup'
    __tcl_members__ = [
            TclMember('framesSent', type=int, flags=FLAG_RDONLY),
            TclMember('frameRate', type=int, flags=FLAG_RDONLY),
    ]

    def __init__(self, parent, group_id):
        super(self.__class__, self).__init__(uri=group_id, parent=parent)


class IxeCapture(IxeObject):
    __tcl_command__ = 'capture'
    __tcl_members__ = [
            TclMember('nPackets', type=int, flags=FLAG_RDONLY),
    ]

    def __init__(self, parent):
        super(self.__class__, self).__init__(uri=parent.uri, parent=parent)


class IxeCaptureBuffer(IxeObject):
    __tcl_command__ = 'captureBuffer'
    __tcl_commands__ = ['export']

    def __init__(self, parent, num_frames):
        super(self.__class__, self).__init__(uri=parent.uri, parent=parent)
        self.num_frames = num_frames

    def ix_command(self, command, *args, **kwargs):
        return self.api.call(('captureBuffer {}' + len(args) * ' {}').format(command, *args))

    def ix_get(self, member=None, force=False):
        self.api.call_rc('captureBuffer get {} 1 {}'.format(self.uri, self.num_frames))


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
            port.api.call_rc('packetGroupStats get {} 0 65536'.format(port.uri))
            if len(port.streams):
                port.api.call_rc('streamTransmitStats get {} 1 4096'.format(port.uri))
        time.sleep(1)
        for port in session.ports.values():
            if len(port.streams):
                port.api.call_rc('streamTransmitStats get {} 1 4096'.format(port.uri))
            for stream_name, stream in port.streams.items():
                stream_stats = IxePgStats(stream).get_attributes(FLAG_RDONLY)
                stream_stats_tx = IxeStreamTxStats(port, stream.uri[-1]).get_attributes(FLAG_RDONLY).items()
                stream_stats.update({c + '_tx': v for c, v in stream_stats_tx})
                self.statistics[stream_name] = stream_stats
