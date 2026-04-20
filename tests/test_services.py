import json
import os
import tempfile
import pytest

from db_plugin.models.config import ConnectionConfig, FakeDataConfig
from db_plugin.models.schema import ColumnSchema, TableSchema
from db_plugin.services.connection_manager import ConnectionManager
from db_plugin.services.fake_data_generator import FakeDataGenerator, _generate_value, FAKER_METHODS
from db_plugin.services.query_history import QueryHistoryService


class TestConnectionManager:
    @pytest.fixture
    def manager(self, tmp_path):
        config_file = tmp_path / "connections.json"
        return ConnectionManager(config_file=str(config_file))

    def test_add_and_list(self, manager):
        config = ConnectionConfig(
            name="test",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="testdb",
        )
        manager.add(config)
        connections = manager.list()
        assert len(connections) == 1
        assert connections[0].name == "test"

    def test_get_connection(self, manager):
        config = ConnectionConfig(
            name="mydb",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="testdb",
        )
        manager.add(config)
        retrieved = manager.get("mydb")
        assert retrieved is not None
        assert retrieved.database == "testdb"

    def test_get_unknown_returns_none(self, manager):
        assert manager.get("nonexistent") is None

    def test_remove_connection(self, manager):
        config = ConnectionConfig(
            name="tmp",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="testdb",
        )
        manager.add(config)
        assert len(manager.list()) == 1
        manager.remove("tmp")
        assert len(manager.list()) == 0

    def test_switch_connection(self, manager, monkeypatch):
        # Mock DatabaseConnection.connect to avoid needing a real database
        monkeypatch.setattr(
            "db_plugin.core.connection.DatabaseConnection.connect",
            lambda self: None,
        )
        monkeypatch.setattr(
            "db_plugin.core.connection.DatabaseConnection.close",
            lambda self: None,
        )
        config1 = ConnectionConfig(
            name="db1",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="db1",
        )
        config2 = ConnectionConfig(
            name="db2",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="db2",
        )
        manager.add(config1)
        manager.add(config2)
        manager.switch_connection("db1")
        assert manager.active_connection_name == "db1"
        manager.switch_connection("db2")
        assert manager.active_connection_name == "db2"

    def test_switch_to_unknown_raises(self, manager):
        with pytest.raises(ValueError, match="not found"):
            manager.switch_connection("nonexistent")

    def test_persistence(self, tmp_path):
        config_file = tmp_path / "connections.json"
        config = ConnectionConfig(
            name="persistent",
            dialect_name="kingbase",
            host="localhost",
            port=54321,
            username="system",
            password="123456",
            database="testdb",
        )
        manager1 = ConnectionManager(config_file=str(config_file))
        manager1.add(config)
        manager2 = ConnectionManager(config_file=str(config_file))
        assert len(manager2.list()) == 1


class TestFakeDataGenerator:
    def test_generate_value_by_field_name(self):
        from faker import Faker
        config = FakeDataConfig()
        faker = Faker()
        val = _generate_value(ColumnSchema(name="name", data_type="varchar"), faker, config)
        assert isinstance(val, str) and len(val) > 0

    def test_generate_value_by_type_fallback(self):
        from faker import Faker
        config = FakeDataConfig()
        faker = Faker()
        val = _generate_value(ColumnSchema(name="unknown_col", data_type="integer"), faker, config)
        assert isinstance(val, int)

        val = _generate_value(ColumnSchema(name="unknown_col", data_type="text"), faker, config)
        assert isinstance(val, str)

        val = _generate_value(ColumnSchema(name="unknown_col", data_type="boolean"), faker, config)
        assert isinstance(val, bool)

    def test_generate_data(self):
        generator = FakeDataGenerator()
        table = TableSchema(
            name="users",
            columns=[
                ColumnSchema(name="id", data_type="integer", is_primary_key=True),
                ColumnSchema(name="name", data_type="varchar"),
                ColumnSchema(name="email", data_type="varchar"),
            ],
            primary_keys=["id"],
        )
        records = generator.generate(table, count=5)
        assert len(records) == 5
        for record in records:
            assert "name" in record
            assert "email" in record

    def test_generate_with_time_config(self):
        generator = FakeDataGenerator()
        table = TableSchema(
            name="test",
            columns=[
                ColumnSchema(name="created_at", data_type="timestamp"),
            ],
            primary_keys=[],
        )
        records = generator.generate(table, count=3)
        for record in records:
            assert "created_at" in record


class TestQueryHistoryService:
    def test_add_and_list(self, tmp_path):
        db = tmp_path / "history.db"
        svc = QueryHistoryService(db_path=str(db))
        svc.add("SELECT 1", "mydb", "success", 5.0)
        entries = svc.list()
        assert len(entries) == 1
        assert entries[0].sql == "SELECT 1"

    def test_search(self, tmp_path):
        db = tmp_path / "history.db"
        svc = QueryHistoryService(db_path=str(db))
        svc.add("SELECT * FROM users", "mydb", "success", 10.0)
        svc.add("INSERT INTO orders VALUES (1)", "mydb", "success", 3.0)
        results = svc.search("SELECT")
        assert len(results) == 1
        assert "users" in results[0].sql

    def test_toggle_favorite(self, tmp_path):
        db = tmp_path / "history.db"
        svc = QueryHistoryService(db_path=str(db))
        entry_id = svc.add("SELECT 1", "mydb", "success", 1.0)
        svc.toggle_favorite(entry_id)
        entries = svc.list()
        assert entries[0].is_favorite is True

    def test_delete(self, tmp_path):
        db = tmp_path / "history.db"
        svc = QueryHistoryService(db_path=str(db))
        entry_id = svc.add("SELECT 1", "mydb", "success", 1.0)
        svc.delete(entry_id)
        assert len(svc.list()) == 0
