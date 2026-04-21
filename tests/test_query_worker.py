import pytest
from PySide6.QtCore import QCoreApplication
from db_plugin.dialects.kingbase import KingbaseDialect
from db_plugin.core.query_worker import QueryWorker


class TestQueryWorker:
    def test_not_connected_emits_error(self, qtbot):
        """Worker emits error when dialect is not connected."""
        dialect = KingbaseDialect()
        worker = QueryWorker(dialect, "SELECT 1")

        results = []
        errors = []
        worker.finished.connect(lambda r: results.append(r))
        worker.error.connect(lambda e: errors.append(e))

        with qtbot.waitSignal(worker.finished, timeout=5000):
            worker.start()

        assert len(results) == 1
        assert results[0].error_message == "Not connected to database"
        worker.wait()

    def test_cancel_before_start(self, qtbot):
        """Worker respects cancel before run."""
        dialect = KingbaseDialect()
        worker = QueryWorker(dialect, "SELECT 1")

        progress_msgs = []
        worker.progress.connect(lambda m: progress_msgs.append(m))

        worker.cancel()

        with qtbot.waitSignal(worker.finished, timeout=5000):
            worker.start()

        worker.wait()
        assert "Cancelled" in progress_msgs
