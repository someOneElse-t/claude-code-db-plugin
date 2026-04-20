import pytest
from db_plugin.dialects.dialect_base import DialectBase
from db_plugin.dialects.mysql import MySQLDialect
from db_plugin.dialects.kingbase import KingbaseDialect


class TestDialectBase:
    """DialectBase 是抽象类，不能直接实例化。"""

    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            DialectBase()


class TestMySQLDialect:
    """MySQLDialect is fully implemented using pymysql."""

    def test_name_is_mysql(self):
        dialect = MySQLDialect()
        assert dialect.name == "mysql"

    def test_quote_char_is_backtick(self):
        dialect = MySQLDialect()
        assert dialect.quote_char == "`"

    def test_not_connected_returns_error_result(self):
        dialect = MySQLDialect()
        result = dialect.execute_query("SELECT 1")
        assert result.error_message == "Not connected to database"


class TestKingbaseDialect:
    def test_name_is_kingbase(self):
        dialect = KingbaseDialect()
        assert dialect.name == "kingbase"

    def test_quote_char_is_backtick(self):
        dialect = KingbaseDialect()
        assert dialect.quote_char == "`"

    def test_quote_identifier(self):
        dialect = KingbaseDialect()
        assert dialect.quote_identifier("user") == "`user`"
        assert dialect.quote_identifier("my_table") == "`my_table`"

    def test_not_connected_returns_error_result(self):
        dialect = KingbaseDialect()
        result = dialect.execute_query("SELECT 1")
        assert result.error_message == "Not connected to database"
