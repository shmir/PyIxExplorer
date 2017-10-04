
from future.utils import with_metaclass

from trafficgenerator.tgn_object import TgnObject

from ixexplorer.api.ixapi import _MetaIxTclApi


class IxeObject(with_metaclass(_MetaIxTclApi, TgnObject)):

    def __init__(self, **data):
        super(IxeObject, self).__init__(objType=self.__tcl_command__, **data)
        self._data['name'] = self._data['name'].replace(' ', '/')

    def _create(self):
        pass

    def _ix_command(self, command, *args, **kwargs):
        return self.api.call(('{} {} {}' + len(args) * ' {}').
                             format(self.__tcl_command__, command, self.obj_ref(), *args))

    def _ix_get(self, member):
        self.api.call_rc('{} get {}'.format(self.__tcl_command__, self.obj_ref()))

    def _ix_set(self, member):
        self.api.call_rc('{} set {}'.format(self.__tcl_command__, self.obj_ref()))
