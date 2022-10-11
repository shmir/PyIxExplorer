"""
Tests for ixexplorer package.
"""
from pathlib import Path
from typing import List

from trafficgenerator import TgnSutUtils, set_logger

from ixexplorer.ixe_app import IxeApp, init_ixe


class IxeSutUtils(TgnSutUtils):
    """IxExplorer SUT utilities."""

    def ixia(self) -> IxeApp:
        ixia = init_ixe(self.sut["server"]["ip"], self.sut["server"]["port"], rsa_id=self.sut["server"]["rsa_id"])
        ixia.connect(user="pyixexplorer")
        ixia.add(self.sut["server"]["ip"])
        return ixia

    def locations(self) -> List[str]:
        chassis = self.sut["chassis"]["ip"]
        return [f"{chassis}/{port}" for port in self.sut["chassis"]["ports"]]


def _load_configs(ixia: IxeApp, *configs: Path) -> None:
    """Load configuration on reserved ports."""
    for port, cfg in zip(ixia.session.ports.values(), configs):
        port.load_config(cfg)


set_logger()
