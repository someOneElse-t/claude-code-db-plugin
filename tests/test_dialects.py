import pytest
from db_plugin.models.config import ConnectionConfig
from db_plugin.dialects.dialect_base import DialectBase
from db_plugin.dialects.mysql import MySQLDialect
from db_plugin.dialects.kingbase import KingbaseDialect


class TestDialectBase:
    """DialectBase 是抽象类，不能直接实例化。"""

    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            DialectBase()


class TestMySQLDialect:
    """MySQLDialect 是占位，所有方法抛 NotImplementedError。"""

    def test_connect_raises(self):
        dialect = MySQLDialect()
        config = ConnectionConfig(
            name="test",
            dialect_name="mysql",
            host="localhost",
            port=3306,
            username="root",
            password="",
            database="testdb",
        )
        with pytest.raises(NotImplementedError):
            dialect.connect(config)

    def test_execute_query_raises(self):
        dialect = MySQLDialect()
        with pytest.raises(NotImplementedError):
            dialect.execute_query("SELECT 1")

    def test_get_tables_raises(self):
        dialect = MySQLDialect()
        with pytest.raises(NotImplementedError):
            dialect.get_tables()

    def test_name_is_mysql(self):
        dialect = MySQLDialect()
        assert dialect.name == "mysql"

    def test_quote_char_is_backtick(self):
        dialect = MySQLDialect()
        assert dialect.quote_char == "`"


class TestKingbaseDialect:
    def test_name_is_kingbase(self):
        dialect = KingbaseDialect()
        assert dialect.name == "kingbase"

    def test_quote_char_is_double_quote(self):
        dialect = KingbaseDialect()
        assert dialect.quote_char == '"'

    def test_quote_identifier(self):
        dialect = KingbaseDialect()
        assert dialect.quote_identifier("user") == '"user"'
        assert dialect.quote_identifier("my_table") == '"my_table"'

    def test_not_connected_returns_error_result(self):
        dialect = KingbaseDialect()
        result = dialect.execute_query("SELECT 1")
        assert result.error_message == "Not connected to database"
