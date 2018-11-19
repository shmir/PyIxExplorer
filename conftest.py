
def pytest_addoption(parser):
    parser.addoption('--server', action='store', default="192.168.15.23", help="IxTcl server in format ip[:port]")
    parser.addoption('--chassis', action='store', default="192.168.42.61", help="chassis IP address")
    parser.addoption('--port1', action='store', default="1/1", help="module1/port1")
    parser.addoption('--port2', action='store', default="1/2", help="module2/port2")
