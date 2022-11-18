"""
Pytest conftest file.
"""
from pathlib import Path

# pylint: disable=redefined-outer-name
from typing import Iterable, List

import pytest
from trafficgenerator.tgn_conftest import log_level, pytest_addoption, sut  # pylint: disable=unused-import

from ixexplorer.ixe_app import IxeApp
from tests import IxeSutUtils


@pytest.fixture(scope="session")
def sut_utils(sut: dict) -> IxeSutUtils:
    """Yield the sut dictionary from the sut file."""
    return IxeSutUtils(sut)


@pytest.fixture
def ixia(sut_utils: IxeSutUtils) -> Iterable[IxeApp]:
    """Yield connected Ixia object."""
    ixia = sut_utils.ixia()
    yield ixia
    for port in ixia.session.ports.values():
        port.release()
    ixia.disconnect()


@pytest.fixture
def locations(sut_utils: IxeSutUtils) -> List[str]:
    """Yield ports locations."""
    return sut_utils.locations()


def test_save_config(ixia: IxeApp, locations: List[str]) -> None:
    """Save current configuration from port."""
    ixia.session.add_ports(*locations)
    ixia.session.reserve_ports(force=True, clear=False)
    list(ixia.session.ports.values())[0].save_config(Path(__file__).parent.joinpath("configs/test_config.prt"))
