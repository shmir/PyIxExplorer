
from collections import OrderedDict
from future.utils import with_metaclass

from trafficgenerator.tgn_object import TgnObject

from ixexplorer.api.ixapi import _MetaIxTclApi


class IxeObject(with_metaclass(_MetaIxTclApi, TgnObject)):

    session = None

    __get_command__ = 'get'
    __set_command__ = 'set'

    def __init__(self, **data):
        data['objRef'] = self.__tcl_command__ + ' ' + str(data['uri'])
        super(IxeObject, self).__init__(objType=self.__tcl_command__, **data)
        if 'name' not in data:
            self._data['name'] = self.uri.replace(' ', '/')
        if self.parent:
            self.session = self.parent.session
        self.__class__.current_object = None

    def obj_uri(self):
        """
        :return: object URI.
        """
        return str(self._data['uri'])
    uri = property(obj_uri)

    def ix_command(self, command, *args, **kwargs):
        return self.api.call(('{} {} {}' + len(args) * ' {}').
                             format(self.__tcl_command__, command, self.uri, *args))

    def ix_set_default(self):
        self.api.call('{} setDefault'.format(self.__tcl_command__))
        self.__class__.current_object = self

    def ix_get(self, member=None, force=False):
        if (self != self.__class__.current_object or force) and self.__get_command__:
            self.api.call_rc('{} {} {}'.format(self.__tcl_command__, self.__get_command__, self.uri))
        self.__class__.current_object = self

    def ix_set(self, member=None):
        self.api.call_rc('{} {} {}'.format(self.__tcl_command__, self.__set_command__, self.uri))

    def get_attributes(self, flags=0xFF, *attributes):
        attrs_values = OrderedDict()
        if not attributes:
            attributes = [m.attrname for m in self.__tcl_members__]
        for member in self.__tcl_members__:
            if (flags == 0xFF or member.flags & flags) and member.name in attributes:
                attrs_values[member.attrname] = getattr(self, member.attrname)
        return attrs_values

    def get_attribute(self, attribute):
        """ Abstract method - must implement - do not call directly. """
        return getattr(self, attribute)

    def set_attributes(self, **attributes):
        """ Set group of attributes without calling set between attributes regardless of global auto_set.

        Set will be called only after all attributes are set based on global auto_set.

        :param attributes: dictionary of <attribute, value> to set.
        """

        auto_set = IxeObject.get_auto_set()
        IxeObject.set_auto_set(False)
        for name, value in attributes.items():
            setattr(self, name, value)
        if auto_set:
            self.ix_set()
        IxeObject.set_auto_set(auto_set)

    def _reset_current_object(self):
        self.__class__.current_object = None
        for child in self.objects.values():
            child._reset_current_object()

    @classmethod
    def get_auto_set(cls):
        return _MetaIxTclApi.auto_set

    @classmethod
    def set_auto_set(cls, auto_set):
        _MetaIxTclApi.auto_set = auto_set
