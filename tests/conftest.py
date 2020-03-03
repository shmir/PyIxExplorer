
import pytest

server = 'localhost'
chassis = '192.168.65.74'
port1 = '1/1'
port2 = '1/2'


def pytest_addoption(parser):
    parser.addoption('--server', action='store', default=server, help="IxTcl server in format ip[:port]")
    parser.addoption('--chassis', action='store', default=chassis, help="chassis IP address")
    parser.addoption('--port1', action='store', default=port1, help="module1/port1")
    parser.addoption('--port2', action='store', default=port2, help="module2/port2")


@pytest.fixture(autouse=True)
def config(request):
    request.cls.chassis = pytest.config.getoption('--chassis')  # @UndefinedVariable
    request.cls.port1 = '{}/{}'.format(request.cls.chassis, pytest.config.getoption('--port1'))  # @UndefinedVariable
    request.cls.port2 = '{}/{}'.format(request.cls.chassis, pytest.config.getoption('--port2'))  # @UndefinedVariable
    server_ip = pytest.config.getoption('--server')  # @UndefinedVariable
    if server_ip:
        request.cls.server_ip = server_ip.split(':')[0]
        request.cls.server_port = int(server_ip.split(':')[1]) if len(server_ip.split(':')) == 2 else 4555
    else:
        server_ip = request.cls.chassis
        request.cls.server_port = 4555
