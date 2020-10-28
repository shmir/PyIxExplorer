"""
Base class for all IxExplorer package tests.

@author yoram@ignissoft.com
"""

from ixexplorer.ixe_app import IxeApp


def _load_configs(ixia: IxeApp, *configs: str) -> None:
    """ Load configuration on reserved ports. """
    for port, cfg in zip(ixia.session.ports.values(), configs):
        port.load_config(cfg)
