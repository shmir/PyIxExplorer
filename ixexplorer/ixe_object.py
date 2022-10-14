from collections import OrderedDict
from typing import Dict, List, Type

from trafficgenerator.tgn_object import TgnObject

from ixexplorer.api.ixapi import ixe_obj_auto_set, ixe_obj_meta


class IxeObject(TgnObject, metaclass=ixe_obj_meta):

    session = None

    __get_command__ = "get"
    __set_command__ = "set"

    def __init__(self, parent, **data):
        data["objRef"] = self.__tcl_command__ + " " + str(data["uri"])
        super().__init__(parent=parent, objType=self.__tcl_command__, **data)
        if "name" not in data:
            self._data["name"] = self.uri.replace(" ", "/")
        if self.uri and (self.uri.split()[-1]).isdigit():
            self._data["index"] = int(self.uri.split()[-1])
        self.__class__.current_object = None

    def obj_uri(self) -> str:
        """Object URI."""
        return str(self._data["uri"])

    uri = property(obj_uri)

    def get_objects_by_type(self, *types: str) -> List[TgnObject]:
        """Override IxeObject.get_objects_by_type because `type` is an attribute name in some IxExplorer objects."""
        if not types:
            return list(self.objects.values())
        types_l = [o.lower() for o in types]
        return [o for o in self.objects.values() if o.obj_type().lower() in types_l]

    def ix_command(self, command, *args, **kwargs):
        return self.api.call(("{} {} {}" + len(args) * " {}").format(self.__tcl_command__, command, self.uri, *args))

    def ix_set_default(self) -> None:
        self.api.call("{} setDefault".format(self.__tcl_command__))
        self.__class__.current_object = self

    def ix_get(self, member=None, force=False) -> None:
        if (self != self.__class__.current_object or force) and self.__get_command__:
            self.api.call_rc("{} {} {}".format(self.__tcl_command__, self.__get_command__, self.uri))
        self.__class__.current_object = self

    def ix_set(self, member=None) -> None:
        self.api.call_rc("{} {} {}".format(self.__tcl_command__, self.__set_command__, self.uri))

    def get_attributes(self, flags=0xFF, *attributes):
        attrs_values = OrderedDict()
        if not attributes:
            attributes = [m.attrname for m in self.__tcl_members__]
        for member in self.__tcl_members__:
            if (flags == 0xFF or member.flags & flags) and member.name in attributes:
                attrs_values[member.attrname] = getattr(self, member.attrname)
        return attrs_values

    def get_attribute(self, attribute):
        """Abstract method - must implement - do not call directly."""
        return getattr(self, attribute)

    def set_attributes(self, **attributes) -> None:
        """Set group of attributes without calling set between attributes regardless of global auto_set.

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

    @classmethod
    def get_auto_set(cls):
        return ixe_obj_auto_set

    @classmethod
    def set_auto_set(cls, auto_set) -> None:
        global ixe_obj_auto_set
        ixe_obj_auto_set = auto_set

    def _reset_current_object(self) -> None:
        self.__class__.current_object = None
        for child in self.objects.values():
            child._reset_current_object()

    def _get_object(self, field, ixe_object):
        if not hasattr(self, field) or not getattr(self, field):
            setattr(self, field, ixe_object(parent=self))
            getattr(self, field).ix_get()
        return getattr(self, field)

    def _create(self, **attributes: Dict[str, object]) -> str:
        pass

    def get_name(self) -> str:
        pass

    def get_children(self, *types: str) -> List[TgnObject]:
        pass

    def get_objects_from_attribute(self, attribute: str) -> List[TgnObject]:
        pass

    def get_obj_class(self, obj_type: str) -> Type[TgnObject]:
        pass


class IxeObjectObj(IxeObject):
    def ix_get(self, member=None, force=False):
        self.parent.ix_get(member, force)
        super().ix_get(member, force)

    def ix_set(self, member=None):
        super().ix_set(member)
        self.parent.ix_set(member)
