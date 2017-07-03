
from future.utils import with_metaclass

from trafficgenerator.tgn_object import TgnObject

from ixexplorer.api.ixapi import _MetaIxTclApi


attributes_xml = ''


class IxeObject(with_metaclass(_MetaIxTclApi, TgnObject)):

    def __init__(self, **data):
        pass

    def _create(self):
        pass


class IxeStream(IxeObject):
    __tcl_command__ = 'stream'
    __tcl_members__ = [
    ]
