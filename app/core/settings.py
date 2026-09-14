"""Kullanıcı ayarları (QSettings). Blok ve parça boyutu motorun varsayılanlarıdır; kullanıcı
Ayarlar ekranından değiştirmezse motor kendi değerini kullanır."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings

DEFAULT_BLOCK = 200      # gece.py BLOK
DEFAULT_CHUNK = 40       # gece.py CHUNK_SAYFA
DEFAULT_TEST_PAGES = 50


class Settings:
    def __init__(self):
        self.q = QSettings()

    # --- çıktı ---
    @property
    def last_output_root(self) -> Path | None:
        v = self.q.value("cikti/son_klasor", "", type=str)
        return Path(v) if v else None

    @last_output_root.setter
    def last_output_root(self, p: Path | str) -> None:
        self.q.setValue("cikti/son_klasor", str(p))

    # --- motor ---
    @property
    def block_size(self) -> int:
        return int(self.q.value("motor/blok", DEFAULT_BLOCK, type=int) or DEFAULT_BLOCK)

    @block_size.setter
    def block_size(self, v: int) -> None:
        self.q.setValue("motor/blok", int(v))

    @property
    def chunk_size(self) -> int:
        return int(self.q.value("motor/parca", DEFAULT_CHUNK, type=int) or DEFAULT_CHUNK)

    @chunk_size.setter
    def chunk_size(self, v: int) -> None:
        self.q.setValue("motor/parca", int(v))

    @property
    def test_pages(self) -> int:
        return int(self.q.value("motor/test_sayfa", DEFAULT_TEST_PAGES, type=int) or DEFAULT_TEST_PAGES)

    # --- kurulum ---
    @property
    def install_consented(self) -> bool:
        return self.q.value("kurulum/onay", False, type=bool)

    @install_consented.setter
    def install_consented(self, v: bool) -> None:
        self.q.setValue("kurulum/onay", bool(v))

    @property
    def notifications(self) -> bool:
        return self.q.value("bildirim/acik", True, type=bool)

    @notifications.setter
    def notifications(self, v: bool) -> None:
        self.q.setValue("bildirim/acik", bool(v))
