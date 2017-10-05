
from ixexplorer.ixe_object import IxeObject


class Stream(IxeObject):
    __tcl_command__ = 'stream'
    __tcl_members__ = [
                       'bpsRate'
    ]

    __tcl_commands__ = ['export']

    next_free_id = 1

    def __init__(self, parent, stream_id=None):
        if not stream_id:
            stream_id = Stream.next_free_id
            Stream.next_free_id += 1
        super(self.__class__, self).__init__(uri=parent.uri + ' ' + str(stream_id), parent=parent)
