from ixexplorer.api.ixapi import FLAG_RDONLY, TclMember, ixe_obj_meta
from ixexplorer.ixe_object import IxeObject


class IxePortGroup(IxeObject, metaclass=ixe_obj_meta):
    START_TRANSMIT = 7
    STOP_TRANSMIT = 8
    START_CAPTURE = 9
    STOP_CAPTURE = 10
    RESET_STATISTICS = 13
    PAUSE_TRANSMIT = 15
    STEP_TRANSMIT = 16
    TRANSMIT_PING = 17
    TAKE_OWNERSHIP = 40
    TAKE_OWNERSHIP_FORCED = 41
    CLEAR_OWNERSHIP = 42
    CLEAR_OWNERSHIP_FORCED = 43

    __tcl_command__ = "portGroup"
    __tcl_members__ = [
        TclMember("lastTimeStamp", type=int, flags=FLAG_RDONLY),
    ]

    __tcl_commands__ = ["create", "destroy"]

    next_free_id = 1

    def __init__(self, pg_id=None):
        if not pg_id:
            pg_id = IxePortGroup.next_free_id
            IxePortGroup.next_free_id += 1
        super().__init__(parent=self.session, uri=pg_id)

    def add_port(self, port):
        self.ix_command("add", port.uri)

    def del_port(self, port):
        self.ix_command("del", port.uri)

    def _set_command(self, cmd):
        self.api.call_rc("portGroup setCommand {} {}".format(self.uri, cmd))

    def start_transmit(self, blocking=False) -> None:
        """
        :param blocking: True - wait for transmit end, False - return immediately.
        :todo: implement blocking.
        """
        self.set_command(self.START_TRANSMIT)

    def stop_transmit(self) -> None:
        self.set_command(self.STOP_TRANSMIT)

    def start_capture(self) -> None:
        self.set_command(self.START_CAPTURE)

    def stop_capture(self) -> None:
        self.set_command(self.STOP_CAPTURE)

    def reset_statistics(self) -> None:
        self.set_command(self.RESET_STATISTICS)

    def pause_transmit(self) -> None:
        self.set_command(self.PAUSE_TRANSMIT)

    def step_transmit(self) -> None:
        self.set_command(self.STEP_TRANSMIT)

    def transmit_ping(self) -> None:
        self.set_command(self.TRANSMIT_PING)

    def take_ownership(self, force: bool = False) -> None:
        if not force:
            self.set_command(self.TAKE_OWNERSHIP)
        else:
            self.set_command(self.TAKE_OWNERSHIP_FORCED)

    def clear_ownership(self, force: bool = False) -> None:
        if not force:
            self.set_command(self.CLEAR_OWNERSHIP)
        else:
            self.set_command(self.CLEAR_OWNERSHIP_FORCED)
