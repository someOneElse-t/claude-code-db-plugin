"""Local address service for fake data generation."""

import json
import logging
import random
from pathlib import Path

logger = logging.getLogger(__name__)

_DEFAULT_ADDRESSES_FILE = Path(__file__).resolve().parent.parent / "data" / "addresses.json"

_cached_addresses: list[dict] = []
_custom_file: str = ""


def _load_addresses(filepath: str = "") -> list[dict]:
    """Load address data from JSON file."""
    global _cached_addresses, _custom_file
    target = filepath or _custom_file or str(_DEFAULT_ADDRESSES_FILE)

    if _cached_addresses and target == (_custom_file or str(_DEFAULT_ADDRESSES_FILE)):
        return _cached_addresses

    path = Path(target)
    if not path.exists():
        logger.warning("Address file not found: %s, falling back to built-in", target)
        path = _DEFAULT_ADDRESSES_FILE
        if not path.exists():
            logger.error("Built-in address file also missing!")
            return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        _cached_addresses = data if isinstance(data, list) else []
        _custom_file = filepath
        logger.info("Loaded %d addresses from %s", len(_cached_addresses), path)
        return _cached_addresses
    except Exception as e:
        logger.error("Failed to parse address file: %s", e)
        return []


def get_random_address() -> str:
    """Return a random full address (province + city + district)."""
    addresses = _load_addresses()
    if not addresses:
        return "北京市朝阳区"
    addr = random.choice(addresses)
    return f"{addr.get('province', '')}{addr.get('city', '')}{addr.get('district', '')}"


def get_random_province() -> str:
    """Return a random province name."""
    addresses = _load_addresses()
    if not addresses:
        return "北京市"
    return random.choice(addresses).get("province", "")


def get_random_city() -> str:
    """Return a random city name."""
    addresses = _load_addresses()
    if not addresses:
        return "北京市"
    return random.choice(addresses).get("city", "")


def get_random_district() -> str:
    """Return a random district name."""
    addresses = _load_addresses()
    if not addresses:
        return "东城区"
    return random.choice(addresses).get("district", "")


def get_all_provinces() -> list[str]:
    """Return list of unique province names."""
    addresses = _load_addresses()
    seen: set[str] = set()
    result = []
    for addr in addresses:
        p = addr.get("province", "")
        if p and p not in seen:
            seen.add(p)
            result.append(p)
    return result


def set_address_file(filepath: str) -> None:
    """Set a custom address file path and reload."""
    global _cached_addresses, _custom_file
    _custom_file = filepath
    _cached_addresses = []
    _load_addresses()
