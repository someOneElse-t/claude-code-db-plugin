from db_plugin.dialects.dialect_base import DialectBase
from db_plugin.dialects.kingbase import KingbaseDialect
from db_plugin.dialects.mysql import MySQLDialect

DIALECT_REGISTRY = {
    "kingbase": KingbaseDialect,
    "mysql": MySQLDialect,
}


def get_dialect(name: str) -> DialectBase:
    """Get a dialect instance by name."""
    cls = DIALECT_REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown dialect: {name}. Available: {list(DIALECT_REGISTRY.keys())}")
    return cls()


__all__ = ["DialectBase", "KingbaseDialect", "MySQLDialect", "get_dialect", "DIALECT_REGISTRY"]
