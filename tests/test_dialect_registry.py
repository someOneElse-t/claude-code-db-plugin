import pytest
from db_plugin.dialects import get_dialect, get_available_dialects


class TestDialectRegistry:
    def test_get_kingbase(self):
        dialect = get_dialect("kingbase")
        assert dialect.name == "kingbase"

    def test_get_mysql(self):
        dialect = get_dialect("mysql")
        assert dialect.name == "mysql"

    def test_unknown_dialect_raises(self):
        with pytest.raises(ValueError, match="Unknown dialect"):
            get_dialect("oracle")

    def test_available_dialects(self):
        names = get_available_dialects()
        assert "kingbase" in names
        assert "mysql" in names
