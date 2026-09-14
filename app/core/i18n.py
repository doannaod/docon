"""Basit çeviri katmanı: EN / TR / ES.

Yaklaşım: Türkçe kaynak metin doğrudan sözlük anahtarıdır (gettext'teki gibi).
`tr("Gözat…")` → geçerli dile göre çevrilmiş metni döndürür; sözlükte yoksa
Türkçesini olduğu gibi döndürür (kayıp çeviri programı bozmaz).

Dil değişikliği kalıcıdır (QSettings) ama uygulanması için yeniden başlatma
gerekir — arayüzü anında yeniden çizmek yerine basit ve hatasız bir yöntem.
"""
from __future__ import annotations

from PySide6.QtCore import QSettings

LANGUAGES = ["en", "tr", "es"]
LANGUAGE_LABELS = {"en": "English", "tr": "Türkçe", "es": "Español"}
DEFAULT_LANGUAGE = "en"


def current_language() -> str:
    v = QSettings().value("dil/kod", DEFAULT_LANGUAGE, type=str)
    return v if v in LANGUAGES else DEFAULT_LANGUAGE


def set_language(code: str) -> None:
    if code not in LANGUAGES:
        raise ValueError(f"bilinmeyen dil: {code}")
    QSettings().setValue("dil/kod", code)


def tr(text: str, **kwargs) -> str:
    """Türkçe kaynak metni geçerli dile çevirir; sözlükte yoksa aynen döner."""
    lang = current_language()
    if lang != "tr":
        entry = _STRINGS.get(text)
        if entry:
            translated = entry.get(lang)
            if translated is not None:
                text = translated
    return text.format(**kwargs) if kwargs else text


# anahtar: Türkçe kaynak metin -> {"en": ..., "es": ...}
_STRINGS: dict[str, dict[str, str]] = {}


def _load() -> None:
    from app.core import i18n_strings
    _STRINGS.update(i18n_strings.STRINGS)


_load()
