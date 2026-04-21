import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_TRANSLATIONS: dict[str, dict[str, str]] = {}
_CURRENT_LANG: str = "zh_CN"


def _load_translations() -> None:
    """Load all available translation files."""
    global _TRANSLATIONS
    locale_dir = Path(__file__).parent.parent / "data" / "locales"
    for lang_file in locale_dir.glob("*.json"):
        lang = lang_file.stem
        try:
            _TRANSLATIONS[lang] = json.loads(locale_dir.joinpath(lang_file.name).read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning("Failed to load translation %s: %s", lang_file.name, e)
    if not _TRANSLATIONS:
        _TRANSLATIONS["zh_CN"] = {}
        _TRANSLATIONS["en_US"] = {}


def set_language(lang: str) -> None:
    """Set the current language."""
    global _CURRENT_LANG
    _CURRENT_LANG = lang


def get_current_language() -> str:
    return _CURRENT_LANG


def get_available_languages() -> list[str]:
    if not _TRANSLATIONS:
        _load_translations()
    return list(_TRANSLATIONS.keys())


def translate(context: str, key: str) -> str:
    """Translate a key for the given context."""
    if not _TRANSLATIONS:
        _load_translations()
    lang_dict = _TRANSLATIONS.get(_CURRENT_LANG, {})
    if context in lang_dict and key in lang_dict[context]:
        return lang_dict[context][key]
    if key in lang_dict:
        return lang_dict[key]
    zh_dict = _TRANSLATIONS.get("zh_CN", {})
    if context in zh_dict and key in zh_dict[context]:
        return zh_dict[context][key]
    if key in zh_dict:
        return zh_dict[key]
    return key


def _t(context: str, key: str) -> str:
    """Shorthand for translate."""
    return translate(context, key)
