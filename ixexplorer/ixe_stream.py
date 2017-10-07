
from ixexplorer.api.ixapi import TclMember
from ixexplorer.ixe_object import IxeObject


class IxeStream(IxeObject):
    __tcl_command__ = 'stream'
    __tcl_members__ = [
            TclMember('name'),
    ]

    __tcl_commands__ = ['export', 'setDefault', 'write']

    def __init__(self, parent, uri):
        super(self.__class__, self).__init__(uri=uri.replace('/', ' '), parent=parent)

    def remove(self):
        self._ix_command('remove')
        self._ix_command('write')
        self.del_object_from_parent()
