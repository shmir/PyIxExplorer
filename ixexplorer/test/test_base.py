"""
Base class for all IxExplorer package tests.

@author yoram@ignissoft.com
"""

from os import path
import pytest

from trafficgenerator.test.test_tgn import TestTgnBase

from ixexplorer.ixe_app import init_ixe


class TestIxeBase(TestTgnBase):

    TestTgnBase.config_file = path.join(path.dirname(__file__), 'IxExplorer.ini')

    def setup(self):

        super(TestIxeBase, self).setup()

        self.ixia = init_ixe(self.logger, host=self.server_ip, port=self.server_port,
                             rsa_id=self.config.get('IXE', 'rsa_id'))
        self.ixia.connect(self.config.get('IXE', 'user'))
        self.ixia.add(self.chassis)

        self.ports = {}

    def teardown(self):
        for port in self.ports.values():
            port.release()
        self.ixia.disconnect()
        super(TestIxeBase, self).teardown()

    def test_hello_world(self):
        pass

    def _reserve_ports(self, *ports):
        self.ports = self.ixia.session.reserve_ports(ports, force=True)

    def _load_configs(self, *cfgs):
        for port, cfg in zip(self.ports.values(), cfgs):
            port.load_config(cfg)

    def _reserver_and_load(self, *cfgs):
        self._reserve_ports(self.port1, self.port2)
        self._load_configs(*cfgs)
