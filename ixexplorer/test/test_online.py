"""
TestCenter package tests that require actual Ixia chassis and active ports.

Test setup:
Two Ixia ports connected back to back.

@author yoram@ignissoft.com
"""

from ixexplorer.ixe_statistics_view import IxePortsStats, IxeStreamsStats
from ixexplorer.test.test_base import IxeTestBase


class IxExplorerTestBase(IxeTestBase):

    def testStats(self):
        cfg1 = 'c:/configs/stats_config.prt'
        cfg2 = 'c:/configs/stats_config.prt'
        self._load_config(cfg1, cfg2)

        self.ixia.session.start_transmit()

        stats = IxePortsStats()
        stats.read_stats()
        print stats.statistics

        stats = IxeStreamsStats()
        stats.read_stats()
        print stats.statistics

        self.ixia.session.stop_transmit()
