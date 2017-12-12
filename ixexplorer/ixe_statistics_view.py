"""
Classes and utilities to manage IxExplorer statistics views.
"""

import time
from collections import OrderedDict
from enum import Enum

from ixexplorer.api.ixapi import TclMember, FLAG_RDONLY
from ixexplorer.ixe_object import IxeObject
from ixexplorer.ixe_stream import IxePacketGroupStream


class IxeCapFileFormat(Enum):
    cap = 1
    enc = 2
    txt = 3


class IxeStat(IxeObject):
    __tcl_command__ = 'stat'
    __tcl_members__ = [
            TclMember('duplexMode', type=int, flags=FLAG_RDONLY),
            TclMember('link', type=int, flags=FLAG_RDONLY),
            TclMember('lineSpeed', type=int, flags=FLAG_RDONLY),

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

            TclMember('asynchronousFramesSent', type=int, flags=FLAG_RDONLY),
            TclMember('alignmentErrors', type=int, flags=FLAG_RDONLY),
            TclMember('bitsSent', type=int, flags=FLAG_RDONLY),
            TclMember('captureFilter', type=int, flags=FLAG_RDONLY),
            TclMember('captureTrigger', type=int, flags=FLAG_RDONLY),
            TclMember('collisionFrames', type=int, flags=FLAG_RDONLY),
            TclMember('collisions', type=int, flags=FLAG_RDONLY),
            TclMember('dataIntegrityErrors', type=int, flags=FLAG_RDONLY),
            TclMember('dataIntegrityFrames', type=int, flags=FLAG_RDONLY),
            TclMember('dribbleErrors', type=int, flags=FLAG_RDONLY),
            TclMember('droppedFrames', type=int, flags=FLAG_RDONLY),
            TclMember('excessiveCollisionFrames', type=int, flags=FLAG_RDONLY),
            TclMember('fcsErrors', type=int, flags=FLAG_RDONLY),
            TclMember('flowControlFrames', type=int, flags=FLAG_RDONLY),
            TclMember('fragments', type=int, flags=FLAG_RDONLY),
            TclMember('ipChecksumErrors', type=int, flags=FLAG_RDONLY),
            TclMember('ipPackets', type=int, flags=FLAG_RDONLY),
            TclMember('lateCollisions', type=int, flags=FLAG_RDONLY),
            TclMember('oversize', type=int, flags=FLAG_RDONLY),
            TclMember('oversizeAndCrcErrors', type=int, flags=FLAG_RDONLY),
            TclMember('pauseAcknowledge', type=int, flags=FLAG_RDONLY),
            TclMember('pauseEndFrames', type=int, flags=FLAG_RDONLY),
            TclMember('pauseOverwrite', type=int, flags=FLAG_RDONLY),
            TclMember('rxPingReply', type=int, flags=FLAG_RDONLY),
            TclMember('rxPingRequest', type=int, flags=FLAG_RDONLY),
            TclMember('scheduledFramesSent', type=int, flags=FLAG_RDONLY),
            TclMember('sequenceErrors', type=int, flags=FLAG_RDONLY),
            TclMember('sequenceFrames', type=int, flags=FLAG_RDONLY),
            TclMember('symbolErrorFrames', type=int, flags=FLAG_RDONLY),
            TclMember('symbolErrors', type=int, flags=FLAG_RDONLY),
            TclMember('synchErrorFrames', type=int, flags=FLAG_RDONLY),
            TclMember('tcpChecksumErrors', type=int, flags=FLAG_RDONLY),
            TclMember('tcpPackets', type=int, flags=FLAG_RDONLY),
            TclMember('transmitDuration', type=int, flags=FLAG_RDONLY),
            TclMember('txPingReply', type=int, flags=FLAG_RDONLY),
            TclMember('txPingRequest', type=int, flags=FLAG_RDONLY),
            TclMember('udpChecksumErrors', type=int, flags=FLAG_RDONLY),
            TclMember('udpPackets', type=int, flags=FLAG_RDONLY),
            TclMember('undersize', type=int, flags=FLAG_RDONLY),

            TclMember('enableArpStats'),
            TclMember('enableDhcpStats'),
            TclMember('enableDhcpV6Stats'),
            TclMember('enableFcoeStats'),
            TclMember('enableIcmpStats'),
            TclMember('enableIgmpStats'),
            TclMember('enableMacSecStats'),
            TclMember('enablePosExtendedStats'),
            TclMember('enableProtocolServerStats'),
            TclMember('enableValidStats'),
            TclMember('fcoeRxSharedStatType1'),
            TclMember('fcoeRxSharedStatType2'),
    ]
    __tcl_commands__ = ['write']
    __get_command__ = None

    def __init__(self, parent):
        super(IxeStat, self).__init__(uri=parent.uri, parent=parent)

    def set_attributes(self, **attributes):
        super(IxeStat, self).set_attributes(**attributes)
        self.write()


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

    def __init__(self, parent, pg_id):
        super(self.__class__, self).__init__(uri=parent.uri + ' ' + str(pg_id) + ' ' + str(pg_id), parent=parent)


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

    def __init__(self, session):
        self.session = session


class IxePortsStats(IxeStats):

    def __init__(self, session, *ports):
        super(self.__class__, self).__init__(session)
        self.ports = ports if ports else self.session.ports.values()

    def set_attributes(self, **attributes):
        for port in self.ports:
            IxeStatTotal(port).set_attributes(**attributes)

    def read_stats(self, *stats):
        """ Read port statistics from chassis.

        :param stats: list of requested statistics to read, if empty - read all statistics.
        """

        self.statistics = OrderedDict()
        for port in self.ports:
            port_stats = IxeStatTotal(port).get_attributes(FLAG_RDONLY, *stats)
            port_stats.update({c + '_rate': v for c, v in
                               IxeStatRate(port).get_attributes(FLAG_RDONLY, *stats).items()})
            self.statistics[str(port)] = port_stats
        return self.statistics


class IxeStreamsStats(IxeStats):

    def read_stats(self, *stats):
        """ Read stream statistics from chassis.

        :param stats: list of requested statistics to read, if empty - read all statistics.
        """

        self.statistics = OrderedDict()
        for port in self.session.ports.values():
            port.api.call_rc('packetGroupStats get {} 0 65536'.format(port.uri))
            if len(port.streams):
                port.api.call_rc('streamTransmitStats get {} 1 4096'.format(port.uri))
        time.sleep(1)
        for port_tx in self.session.ports.values():
            for stream in port_tx.streams.values():
                stream_stats = {}
                stream_stats_tx = {c + '_tx': v for c, v in
                                   IxeStreamTxStats(port_tx, stream.uri[-1]).get_attributes(FLAG_RDONLY).items()}
                stream_stats['tx'] = stream_stats_tx
                stream_stat_pgid = IxePacketGroupStream(stream).groupId
                stream_stats_pg = OrderedDict()
                for port_rx in self.session.ports.values():
                    stream_stats_pg[port_rx] = IxePgStats(port_rx, stream_stat_pgid).get_attributes(FLAG_RDONLY,
                                                                                                    *stats)
                stream_stats['rx'] = stream_stats_pg
                self.statistics[stream] = stream_stats
