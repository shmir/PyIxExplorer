
from ixexplorer.ixe_object import IxeObject


class Stream(IxeObject):
    __tcl_command__ = 'stream'
    __tcl_members__ = [
    ]

    __tcl_commands__ = ['export', 'write']

    next_free_id = 1

    def __init__(self, parent, stream_id=None):
        if not stream_id:
            stream_id = Stream.next_free_id
            Stream.next_free_id += 1
        super(self.__class__, self).__init__(uri=parent.uri + ' ' + str(stream_id), parent=parent)

    def remove(self):
        self._ix_command('remove')
        self._ix_command('write')
        self.del_object_from_parent()
