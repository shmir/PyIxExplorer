# pylint: disable=redefined-outer-name
from typing import Iterable, List

import pytest
from trafficgenerator.tgn_conftest import log_level, pytest_addoption, sut

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
