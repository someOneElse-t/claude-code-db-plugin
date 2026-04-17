from db_plugin.models.config import ConnectionConfig
from db_plugin.models.schema import ColumnSchema, TableSchema, IndexSchema
from db_plugin.models.result import QueryResult
from db_plugin.models.history import QueryHistoryEntry
from datetime import datetime


class TestConnectionConfig:
    def test_create_config(self):
        config = ConnectionConfig(
            name="mydb",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="testdb",
        )
        assert config.name == "mydb"
        assert config.dialect_name == "kingbase"
        assert config.host == "localhost"
        assert config.port == 54321
        assert config.extra_params == {}

    def test_default_extra_params(self):
        config = ConnectionConfig(
            name="test",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="testdb",
        )
        assert config.extra_params == {}


class TestTableSchema:
    def test_create_table_schema(self):
        col = ColumnSchema(
            name="id",
            data_type="integer",
            is_nullable=False,
            default_value=None,
            is_primary_key=True,
            comment="Primary key",
        )
        table = TableSchema(
            name="users",
            columns=[col],
            primary_keys=["id"],
            indexes=[],
        )
        assert table.name == "users"
        assert len(table.columns) == 1
        assert "id" in table.primary_keys


class TestQueryResult:
    def test_create_result(self):
        result = QueryResult(
            columns=["id", "name"],
            rows=[{"id": 1, "name": "Alice"}],
            row_count=1,
            execution_time_ms=15.0,
            error_message=None,
        )
        assert result.row_count == 1
        assert result.error_message is None

    def test_error_result(self):
        result = QueryResult(
            columns=[],
            rows=[],
            row_count=0,
            execution_time_ms=0,
            error_message="connection refused",
        )
        assert result.error_message == "connection refused"


class TestQueryHistoryEntry:
    def test_create_entry(self):
        entry = QueryHistoryEntry(
            id=1,
            sql="SELECT * FROM users",
            connection_name="mydb",
            timestamp=datetime.now(),
            status="success",
            execution_time_ms=10.0,
            is_favorite=False,
        )
        assert entry.status == "success"
        assert entry.is_favorite is False
