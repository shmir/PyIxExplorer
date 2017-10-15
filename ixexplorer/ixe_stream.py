
from ixexplorer.api.ixapi import TclMember, MacStr, FLAG_RDONLY
from ixexplorer.ixe_object import IxeObject


class IxeStream(IxeObject):
    __tcl_command__ = 'stream'
    __tcl_members__ = [
            TclMember('bpsRate', type=int),
            TclMember('da', type=MacStr),
            TclMember('frameSizeType', type=int),
            TclMember('name'),
            TclMember('sa', type=MacStr),

            #Stream_Control
            TclMember('rateMode', type=int),
            TclMember('percentPacketRate', type=float),
    ]

    __tcl_commands__ = ['export', 'write']

    last_object = None

    def __init__(self, parent, uri):
        super(self.__class__, self).__init__(uri=uri.replace('/', ' '), parent=parent)

    def remove(self):
        self._ix_command('remove')
        self._ix_command('write')
        self.del_object_from_parent()

    def ix_set_default(self):
        super(self.__class__, self).ix_set_default()
        if IxeStream.last_object:
            for stream_object in [o for o in IxeStream.last_object.__dict__.values() if isinstance(o, IxeStreamObj)]:
                stream_object.ix_set_default()
        IxeStream.last_object = self

    def get_ip(self):
        return self.get_object('_ip', IxeIp)
    ip = property(get_ip)

    def get_protocol(self):
        return self.get_object('_protocol', IxeProtocol)
    protocol = property(get_protocol)

    def get_weightedRandomFramesize(self):
        return self.get_object('_weightedRandomFramesize', IxeWeightedRandomFramesize)
    weightedRandomFramesize = property(get_weightedRandomFramesize)

    def get_object(self, field, ixe_object):
        if not hasattr(self, field):
            setattr(self, field, ixe_object(parent=self))
            getattr(self, field).ix_set_default()
        return getattr(self, field)


class IxeStreamObj(IxeObject):

    def __init__(self, parent):
        super(IxeStreamObj, self).__init__(uri=parent.uri[:-2], parent=parent)

    def ix_command(self, command, *args, **kwargs):
        rc = self.api.call(('{} {}' + len(args) * ' {}').format(self.__tcl_command__, command, *args))
        self.ix_set()
        return rc

    def ix_get(self, member=None):
        self.parent.ix_get(member)
        super(IxeStreamObj, self).ix_get(member)

    def ix_set(self, member=None):
        super(IxeStreamObj, self).ix_set(member)
        self.parent.ix_set(member)


class IxeProtocol(IxeStreamObj):
    __tcl_command__ = 'protocol'
    __tcl_members__ = [
            TclMember('ethernetType'),
            TclMember('name'),
    ]

    def ix_get(self, member=None):
        self.parent.ix_get(member)

    def ix_set(self, member=None):
        pass


class IxeIp(IxeStreamObj):
    __tcl_command__ = 'ip'
    __tcl_members__ = [
            TclMember('destIpAddr'),
            TclMember('destIpAddrMode'),
            TclMember('sourceIpAddr'),
            TclMember('sourceIpAddrMode'),
            TclMember('ttl', type=int),
    ]


class IxeWeightedRandomFramesize(IxeStreamObj):
    __tcl_command__ = 'weightedRandomFramesize'
    __tcl_members__ = [
            TclMember('center', type=float),
            TclMember('pairList', flags=FLAG_RDONLY),
            TclMember('randomType', type=int),
            TclMember('weight', type=int),
            TclMember('widthAtHalf', type=float),
    ]
    __tcl_commands__ = ['addPair', 'delPair']
