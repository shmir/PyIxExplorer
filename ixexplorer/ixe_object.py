
from future.utils import with_metaclass

from trafficgenerator.tgn_object import TgnObject

from ixexplorer.api.ixapi import _MetaIxTclApi


attributes_xml = ''


class IxeObject(with_metaclass(_MetaIxTclApi, TgnObject)):

    def __init__(self, **data):
        super(IxeObject, self).__init__(**data)
        self._data['name'] = self._data['name'].replace(' ', '/')

    def _create(self):
        pass

    def _ix_command(self, command, *args, **kwargs):
        return self.api.call(('{} {} {}' + len(args) * ' {}').
                             format(self.__tcl_command__, command, self.obj_ref(), *args))


class IxeStream(IxeObject):
    __tcl_command__ = 'stream'
    __tcl_members__ = [
    ]
