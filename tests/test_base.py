"""
Base class for all IxExplorer package tests.

@author yoram@ignissoft.com
"""

from ixexplorer.ixe_app import IxeApp


def _load_configs(ixia: IxeApp, *cfgs: str) -> None:
    """ Load configuration on reserved ports. """
    for port, cfg in zip(ixia.session.ports.values(), cfgs):
        port.load_config(cfg)
