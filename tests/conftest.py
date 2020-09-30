
import logging
from pathlib import Path
from typing import List

import pytest
from _pytest.config.argparsing import Parser

from trafficgenerator.tgn_conftest import (tgn_pytest_addoption, pytest_generate_tests, logger, api, server,
                                           server_properties)
from ixexplorer.ixe_app import init_ixe, IxeApp

RSA_ID = 'C:/Program Files (x86)/Ixia/IxOS/9.00.1900.10/TclScripts/lib/ixTcl1.0/id_rsa'


def pytest_addoption(parser: Parser) -> None:
    """ Add options to allow the user to determine which APIs and servers to test. """
    tgn_pytest_addoption(parser, Path(__file__).parent.joinpath('test_config.py').as_posix())


@pytest.fixture
def ixia(logger: logging.Logger, server_properties: dict) -> IxeApp:
    """ Yields connected Ixia object. """
    server, port = server_properties['server'].split(':')
    ixia = init_ixe(logger, server, int(port), rsa_id=RSA_ID)
    ixia.connect(user='pyixexplorer')
    yield ixia
    for port in ixia.session.ports.values():
        port.release()
    ixia.disconnect()


@pytest.fixture
def locations(ixia: IxeApp, server_properties: dict) -> List[str]:
    """ Yields ports locations. """
    for chassis in [l.split('/')[0] for l in server_properties['locations']]:
        ixia.add(chassis)
    yield server_properties['locations']
