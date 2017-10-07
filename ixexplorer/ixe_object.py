
from future.utils import with_metaclass

from trafficgenerator.tgn_object import TgnObject

from ixexplorer.api.ixapi import _MetaIxTclApi


class IxeObject(with_metaclass(_MetaIxTclApi, TgnObject)):

    session = None

    def __init__(self, **data):
        data['objRef'] = self.__tcl_command__ + ' ' + str(data['uri'])
        super(IxeObject, self).__init__(objType=self.__tcl_command__, **data)
        self._data['name'] = self.uri.replace(' ', '/')
        self.__class__.current_object = None

    def obj_uri(self):
        """
        :return: object URI.
        """
        return str(self._data['uri'])
    uri = property(obj_uri)

    def _ix_command(self, command, *args, **kwargs):
        return self.api.call(('{} {} {}' + len(args) * ' {}').
                             format(self.__tcl_command__, command, self.uri, *args))

    def _ix_get(self):
        if self != self.__class__.current_object:
            self.api.call_rc('{} get {}'.format(self.__tcl_command__, self.uri))
        self.__class__.current_object = self

    def _ix_set(self):
        self.api.call_rc('{} set {}'.format(self.__tcl_command__, self.uri))
