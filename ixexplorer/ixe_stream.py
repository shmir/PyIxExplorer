
from ixexplorer.ixe_object import IxeObject


class Stream(IxeObject):
    __tcl_command__ = 'stream'
    __tcl_members__ = [
    ]

    __tcl_commands__ = ['export']

    def __init__(self, tcl, parent, id):
        self.port = parent
        self.id = id
        self._api = tcl

    def _ix_get(self, member):
        self._api.call_rc('stream get {} {} {} {}'.format(*self._stream_id()))

    def _ix_set(self, member):
        self._api.call_rc('stream set {} {} {} {}'.format(*self._stream_id()))

    def _ix_command(self, command, *args):
        return self._api.call(('stream {} {} {} {} {}' + len(args) * ' {}').
                              format(command, *(self._stream_id() + args)))

    def _stream_id(self):
        return self.port._port_id() + (self.id,)

    def __str__(self):
        return '%d/%d/%d/%d' % self._stream_id()
