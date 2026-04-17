import pytest
from db_plugin.models.config import ConnectionConfig
from db_plugin.core.connection import DatabaseConnection
from db_plugin.core.executor import QueryExecutor
from db_plugin.dialects.kingbase import KingbaseDialect


class TestDatabaseConnection:
    def test_create_connection(self):
        config = ConnectionConfig(
            name="test",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="testdb",
        )
        conn = DatabaseConnection(config)
        assert conn.dialect is not None
        assert isinstance(conn.dialect, KingbaseDialect)
        assert conn.is_connected is False

    def test_unknown_dialect_raises(self):
        config = ConnectionConfig(
            name="test",
            dialect_name="unknown",
            host="localhost",
            port=1234,
            username="root",
            password="",
            database="testdb",
        )
        with pytest.raises(ValueError, match="Unknown dialect"):
            DatabaseConnection(config)

    def test_get_dialect(self):
        config = ConnectionConfig(
            name="test",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="testdb",
        )
        conn = DatabaseConnection(config)
        assert conn.get_dialect() is conn.dialect


class TestQueryExecutor:
    """QueryExecutor tests require a real connection, so we test basic construction."""

    def test_create_executor(self):
        config = ConnectionConfig(
            name="test",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="testdb",
        )
        conn = DatabaseConnection(config)
        executor = QueryExecutor(conn)
        assert executor.connection is conn
