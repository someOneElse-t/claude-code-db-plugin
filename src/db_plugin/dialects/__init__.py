import logging
from importlib import import_module
from importlib.metadata import entry_points

from db_plugin.dialects.dialect_base import DialectBase

logger = logging.getLogger(__name__)

# Built-in dialects loaded eagerly
_BUILTIN_DIALECTS = {
    "kingbase": "db_plugin.dialects.kingbase",
    "mysql": "db_plugin.dialects.mysql",
}

_LOADED_DIALECTS: dict[str, type[DialectBase]] | None = None


def _load_dialects() -> dict[str, type[DialectBase]]:
    """Load all dialect classes from built-ins and entry points."""
    global _LOADED_DIALECTS
    if _LOADED_DIALECTS is not None:
        return _LOADED_DIALECTS

    result: dict[str, type[DialectBase]] = {}

    # Load built-in dialects
    for name, module_path in _BUILTIN_DIALECTS.items():
        module = import_module(module_path)
        # Find the dialect class in the module (ends with "Dialect", not DialectBase)
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and attr_name.endswith("Dialect")
                and attr_name != "DialectBase"
                and issubclass(attr, DialectBase)
            ):
                result[name] = attr
                break

    # Discover plugin dialects via entry points
    try:
        eps = entry_points(group="db_plugin.dialects")
    except TypeError:
        # Python < 3.10 compatibility
        eps = entry_points().get("db_plugin.dialects", [])

    for ep in eps:
        try:
            cls = ep.load()
            if issubclass(cls, DialectBase):
                result[ep.name] = cls
                logger.info("Loaded dialect plugin: %s", ep.name)
        except Exception as e:
            logger.warning("Failed to load dialect plugin %s: %s", ep.name, e)

    _LOADED_DIALECTS = result
    return result


def get_dialect(name: str) -> DialectBase:
    """Get a dialect instance by name."""
    dialects = _load_dialects()
    cls = dialects.get(name)
    if cls is None:
        raise ValueError(f"Unknown dialect: {name}. Available: {list(dialects.keys())}")
    return cls()


def get_available_dialects() -> list[str]:
    """Return list of available dialect names."""
    return list(_load_dialects().keys())


__all__ = ["DialectBase", "get_dialect", "get_available_dialects"]
