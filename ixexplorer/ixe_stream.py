
from ixexplorer.api.ixapi import TclMember, MacStr, FLAG_RDONLY
from ixexplorer.ixe_object import IxeObject


class IxeStream(IxeObject):
    __tcl_command__ = 'stream'
    __tcl_members__ = [
            TclMember('adjustMask'),
            TclMember('asyncIntEnable'),
            TclMember('bpsRate', type=float),
            TclMember('da', type=MacStr),
            TclMember('daMaskSelect'),
            TclMember('daMaskValue', type=MacStr),
            TclMember('daRepeatCounter'),
            TclMember('daStep', type=int),
            TclMember('dataPattern'),
            TclMember('dma'),
            TclMember('enable'),
            TclMember('enableDaContinueFromLastValue'),
            TclMember('enableIbg'),
            TclMember('enableIncrFrameBurstOverride'),
            TclMember('enableIsg'),
            TclMember('enableSaContinueFromLastValue'),
            TclMember('enableSourceInterface'),
            TclMember('enableStatistic'),
            TclMember('enableSuspend'),
            TclMember('enableTimestamp'),
            TclMember('enforceMinGap'),
            TclMember('fcs'),
            TclMember('fpsRate', float),
            TclMember('framesize', int),
            TclMember('frameSizeMAX', int),
            TclMember('frameSizeMIN', int),
            TclMember('frameSizeStep', int),
            TclMember('frameSizeType', type=int),
            TclMember('frameType'),
            TclMember('gapUnit'),
            TclMember('ibg', float),
            TclMember('ifg', float),
            TclMember('ifgMAX', float),
            TclMember('ifgMIN', float),
            TclMember('ifgType'),
            TclMember('isg', float),
            TclMember('loopCount', int),
            TclMember('name'),
            TclMember('numBursts', int),
            TclMember('numDA', type=int),
            TclMember('numFrames', float),
            TclMember('numSA', type=int),
            TclMember('pattern', list),
            TclMember('patternType'),
            TclMember('percentPacketRate', type=float),
            TclMember('preambleData'),
            TclMember('preambleSize', int),
            TclMember('priorityGroup', int),
            TclMember('rateMode, int'),
            TclMember('rateMode', type=int),
            TclMember('returnToId', int),
            TclMember('rxTriggerEnable'),
            TclMember('sa', type=MacStr),
            TclMember('saMaskSelect'),
            TclMember('saMaskValue', type=MacStr),
            TclMember('saRepeatCounter'),
            TclMember('saStep', type=int),
            TclMember('sourceInterfaceDescription'),

    ]

    __tcl_commands__ = ['export', 'write']

    last_object = None

    def __init__(self, parent, uri):
        super(self.__class__, self).__init__(uri=uri.replace('/', ' '), parent=parent)

    def remove(self):
        self.ix_command('remove')
        self.ix_command('write')
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

    def get_tcp(self):
        return self.get_object('_tcp', IxeTcp)
    tcp = property(get_tcp)

    def get_udp(self):
        return self.get_object('_udp', IxeUdp)
    udp = property(get_udp)

    def get_protocol(self):
        return self.get_object('_protocol', IxeProtocol)
    protocol = property(get_protocol)

    def get_weightedRandomFramesize(self):
        return self.get_object('_weightedRandomFramesize', IxeWeightedRandomFramesize)
    weightedRandomFramesize = property(get_weightedRandomFramesize)

    def get_udf(self):
        return self.get_object('_udf', IxeUdf)
    udf = property(get_udf)


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

    def ix_get(self, member=None, force=False):
        self.parent.ix_get(member, force)
        super(IxeStreamObj, self).ix_get(member, force)

    def ix_set(self, member=None):
        super(IxeStreamObj, self).ix_set(member)
        self.parent.ix_set(member)


class IxeProtocol(IxeStreamObj):
    __tcl_command__ = 'protocol'
    __tcl_members__ = [
            TclMember('appName'),
            TclMember('ethernetType'),
            TclMember('name'),

    ]

    def ix_get(self, member=None, force=False):
        self.parent.ix_get(member, force)

    def ix_set(self, member=None):
        pass


class IxeIp(IxeStreamObj):
    __tcl_command__ = 'ip'
    __tcl_members__ = [
            TclMember('assuredForwardingClass', type=int),
            TclMember('assuredFowardingPrecedence', type=int),
            TclMember('checksum'),
            TclMember('classSelector', type=int),
            TclMember('cost', type=int),
            TclMember('delay', type=int),
            TclMember('destClass', type=int),
            TclMember('destIpAddr'),
            TclMember('destIpAddrMode'),
            TclMember('destIpAddrRepeatCount', type=int),
            TclMember('destIpMask'),
            TclMember('dscpMode', type=int),
            TclMember('dscpValue'),
            TclMember('enableDestSyncFromPpp', type=bool),
            TclMember('enableHeaderLengthOverride', type=bool),
            TclMember('enableSourceSyncFromPpp', type=bool),
            TclMember('fragment', type=int),
            TclMember('fragmentOffset', type=int),
            TclMember('headerLength'),
            TclMember('identifier', type=int),
            TclMember('ipProtocol', type=int),
            TclMember('lastFragment', type=int),
            TclMember('lengthOverride', type=bool),
            TclMember('options'),
            TclMember('precedence', type=int),
            TclMember('qosMode', type=int),
            TclMember('reliability', type=int),
            TclMember('reserved', type=int),
            TclMember('sourceCommand', type=int),
            TclMember('sourceIpAddr'),
            TclMember('sourceIpAddrMode'),
            TclMember('sourceIpAddrRepeatCount', type=int),
            TclMember('sourceIpMask'),
            TclMember('throughput', type=int),
            TclMember('totalLength', type=int),
            TclMember('ttl', type=int),
            TclMember('useValidChecksum'),

    ]


class IxeTcp(IxeStreamObj):
    __tcl_command__ = 'tcp'
    __tcl_members__ = [
            TclMember('acknowledgementNumber', type=int),
            TclMember('acknowledgeValid'),
            TclMember('checksum'),
            TclMember('destPort', type=int),
            TclMember('finished'),
            TclMember('offset', type=int),
            TclMember('pushFunctionValid'),
            TclMember('resetConnection'),
            TclMember('sequenceNumber', type=int),
            TclMember('sourcePort', type=int),
            TclMember('synchronize'),
            TclMember('urgentPointer', type=int),
            TclMember('urgentPointerValid'),
            TclMember('useValidChecksum'),
            TclMember('window', type=int),

    ]


class IxeUdp(IxeStreamObj):
    __tcl_command__ = 'udp'
    __tcl_members__ = [
            TclMember('checksum', type=int),
            TclMember('checksumMode'),
            TclMember('destPort', type=int),
            TclMember('enableChecksumOverride'),
            TclMember('length', type=int),
            TclMember('lengthOverride'),
            TclMember('sourcePort', type=int),

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


class IxePacketGroupStream(IxeStreamObj):
    __tcl_command__ = 'packetGroup'
    __tcl_members__ = [
            TclMember('groupId', type=int),
    ]
    __get_command__ = 'getTx'
    __set_command__ = 'setTx'

    def __init__(self, parent):
        super(IxeStreamObj, self).__init__(uri=parent.uri, parent=parent)


class IxeUdf(IxeStreamObj):
    __tcl_command__ = 'udf'
    __tcl_members__ = [
            TclMember('bitOffset', int),
            TclMember('cascadeType', int),
            TclMember('chainFrom', int),
            TclMember('continuousCount'),
            TclMember('counterMode', int),
            TclMember('countertype', int),
            TclMember('enable'),
            TclMember('enableCascade'),
            TclMember('enableIndexMode'),
            TclMember('enableKillBitMode'),
            TclMember('enableSkipZerosAndOnes'),
            TclMember('initval'),
            TclMember('innerLoop'),
            TclMember('innerRepeat'),
            TclMember('innerStep'),
            TclMember('killBitUDFSize'),
            TclMember('linearCoefficient'),
            TclMember('linearCoefficientEnable'),
            TclMember('linearCoefficientLoopCount0'),
            TclMember('linearCoefficientLoopCount2'),
            TclMember('maskselect'),
            TclMember('maskval'),
            TclMember('offset'),
            TclMember('random'),
            TclMember('repeat', int),
            TclMember('skipMaskBits'),
            TclMember('step', int),
            TclMember('tripleNestedLoop0Increment'),
            TclMember('udfSize'),
            TclMember('updown', int),
            TclMember('valueList'),
            TclMember('valueRepeatCount'),

    ]

