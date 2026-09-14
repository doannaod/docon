"""Ayarlar (Kapsam v2): çıktı, bildirim, motor varsayılanları, ham temizlik, sürüm."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QHBoxLayout, QLineEdit, QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from app import APP_NAME, __version__
from app.core.i18n import LANGUAGE_LABELS, LANGUAGES, current_language, set_language, tr
from app.core.paths import format_bytes
from app.core.settings import DEFAULT_BLOCK, DEFAULT_CHUNK, DEFAULT_TEST_PAGES, Settings
from app.ui import theme
from app.ui.widgets import Card, label, scroll_body


class SettingsPage(QWidget):
    clean_requested = Signal()
    changed = Signal()

    def __init__(self, settings: Settings, parent: QWidget | None = None):
        super().__init__(parent)
        self.s = settings
        root = scroll_body(self, spacing=18)
        head = QVBoxLayout(); head.setSpacing(4)
        head.addWidget(label(tr("Ayarlar"), "H2")); head.addWidget(label(tr("Değişiklikler anında kaydedilir."), "Subtle"))
        root.addLayout(head)

        # Dil
        lc = Card()
        lc.body.addWidget(label(tr("Dil"), "SectionTitle"))
        lrow = QHBoxLayout(); lrow.setSpacing(8)
        lrow.addWidget(label(tr("Arayüz dili"), "Soft")); lrow.addStretch()
        self.language = QComboBox()
        for code in LANGUAGES:
            self.language.addItem(LANGUAGE_LABELS[code], code)
        self.language.currentIndexChanged.connect(self._on_language_changed)
        lrow.addWidget(self.language)
        lc.body.addLayout(lrow)
        self.language_hint = label("", "TileLabel", wrap=True); lc.body.addWidget(self.language_hint)
        root.addWidget(lc)

        # Çıktı
        c = Card()
        c.body.addWidget(label(tr("Çıktı"), "SectionTitle"))
        c.body.addWidget(label(tr("Varsayılan çıktı klasörü (son kullanılan otomatik gelir)"), "Soft"))
        row = QHBoxLayout(); row.setSpacing(8)
        self.out_edit = QLineEdit(); self.out_edit.setReadOnly(True); row.addWidget(self.out_edit, 1)
        b = QPushButton(tr("Gözat…")); b.setObjectName("Small"); b.clicked.connect(self._browse); row.addWidget(b)
        c.body.addLayout(row)
        nrow = QHBoxLayout(); nrow.addWidget(label(tr("Kitap bitince Windows bildirimi göster"))); nrow.addStretch()
        self.notify = QCheckBox(""); self.notify.toggled.connect(self._save); nrow.addWidget(self.notify)
        c.body.addLayout(nrow)
        root.addWidget(c)

        # Motor
        m = Card()
        mh = QHBoxLayout(); mh.addWidget(label(tr("Motor"), "SectionTitle")); mh.addStretch(); mh.addWidget(label(tr("Sistem varsayılanları önerilir"), "Subtle"))
        m.body.addLayout(mh)
        grid = QHBoxLayout(); grid.setSpacing(12)
        self.block = QSpinBox(); self.block.setRange(20, 1000); self.block.setSingleStep(20)
        self.chunk = QSpinBox(); self.chunk.setRange(10, 200); self.chunk.setSingleStep(5)
        self.test = QSpinBox(); self.test.setRange(10, 200); self.test.setSingleStep(10)
        for t, w, d in ((tr("Blok boyutu (sayfa)"), self.block, DEFAULT_BLOCK),
                        (tr("Parça boyutu (sayfa)"), self.chunk, DEFAULT_CHUNK),
                        (tr("Test koşusu (sayfa)"), self.test, DEFAULT_TEST_PAGES)):
            col = QVBoxLayout(); col.setSpacing(6)
            cap = QHBoxLayout(); cap.addWidget(label(t, "Soft")); cap.addStretch(); cap.addWidget(label(tr("varsayılan {d}", d=d), "TileLabel"))
            col.addLayout(cap)
            w.setMinimumHeight(36); w.setStyleSheet(f"QSpinBox {{ padding: 0 8px; border: 1px solid {theme.BORDER_STRONG}; border-radius: 6px; background: {theme.INPUT_BG}; }}")
            w.setToolTip(tr("Varsayılan: {d}", d=d))
            col.addWidget(w)
            w.valueChanged.connect(self._save)
            grid.addLayout(col, 1)
        m.body.addLayout(grid)
        m.body.addWidget(label(tr("Blok: OCR kaç sayfalık parçalarla yapılır. Parça: içindekiler yoksa kitap kaç sayfalık dosyalara bölünür."), "TileLabel", wrap=True))
        reset = QPushButton(tr("Varsayılanlara dön")); reset.setObjectName("Link"); reset.setCursor(Qt.PointingHandCursor); reset.clicked.connect(self._reset)
        m.body.addWidget(reset, 0, Qt.AlignRight)
        root.addWidget(m)

        # Depolama
        d = Card(spacing=10)
        d.body.addWidget(label(tr("Depolama"), "SectionTitle"))
        drow = QHBoxLayout(); drow.setSpacing(12)
        col = QVBoxLayout(); col.setSpacing(2)
        col.addWidget(label(tr("Ham klasörleri temizle")))
        self.clean_desc = label("", "TileLabel", wrap=True); col.addWidget(self.clean_desc)
        drow.addLayout(col, 1)
        self.btn_clean = QPushButton(tr("Temizle")); self.btn_clean.setObjectName("Small"); self.btn_clean.clicked.connect(self.clean_requested)
        drow.addWidget(self.btn_clean, 0, Qt.AlignVCenter)
        d.body.addLayout(drow)
        self.clean_result = label("", "Subtle"); self.clean_result.setStyleSheet(f"color: {theme.SUCCESS}; font-size: 9pt;"); d.body.addWidget(self.clean_result); self.clean_result.hide()
        root.addWidget(d)

        # Hakkında
        a = Card(padding=14)
        arow = QHBoxLayout()
        col2 = QVBoxLayout(); col2.setSpacing(2)
        col2.addWidget(label(f"{APP_NAME} {__version__}", "SectionTitle"))
        self.about = label("", "TileLabel", wrap=True); col2.addWidget(self.about)
        arow.addLayout(col2, 1)
        self.update_state = label("", "Subtle"); arow.addWidget(self.update_state)
        a.body.addLayout(arow)
        root.addWidget(a)
        self.load()

    def load(self) -> None:
        for w in (self.block, self.chunk, self.test, self.notify, self.language):
            w.blockSignals(True)
        self.out_edit.setText(str(self.s.last_output_root or ""))
        self.notify.setChecked(self.s.notifications)
        self.block.setValue(self.s.block_size); self.chunk.setValue(self.s.chunk_size); self.test.setValue(self.s.test_pages)
        self.language.setCurrentIndex(LANGUAGES.index(current_language()))
        for w in (self.block, self.chunk, self.test, self.notify, self.language):
            w.blockSignals(False)

    def set_clean_info(self, count: int, size: int) -> None:
        if count:
            self.clean_desc.setText(tr("Bitmiş kitapların ara dosyaları. {n} kitap · {size}. Silmek çıktıyı etkilemez.",
                                       n=count, size=format_bytes(size)))
        else:
            self.clean_desc.setText(tr("Temizlenecek ara dosya yok."))
        self.btn_clean.setEnabled(count > 0)

    def show_clean_result(self, freed: int) -> None:
        self.clean_result.setText(tr("✓ Silindi, {size} boşaldı.", size=format_bytes(freed))); self.clean_result.show()

    def set_about(self, text: str, update_text: str = "") -> None:
        self.about.setText(text); self.update_state.setText(update_text)

    def _save(self, *_):
        self.s.notifications = self.notify.isChecked()
        self.s.block_size = self.block.value(); self.s.chunk_size = self.chunk.value()
        self.s.q.setValue("motor/test_sayfa", self.test.value())
        self.changed.emit()

    def _reset(self) -> None:
        self.block.setValue(DEFAULT_BLOCK); self.chunk.setValue(DEFAULT_CHUNK); self.test.setValue(DEFAULT_TEST_PAGES)

    def _browse(self) -> None:
        d = QFileDialog.getExistingDirectory(self, tr("Varsayılan çıktı klasörü"), self.out_edit.text() or str(Path.home()))
        if d:
            self.s.last_output_root = d; self.out_edit.setText(d); self.changed.emit()

    def _on_language_changed(self, index: int) -> None:
        code = self.language.itemData(index)
        if code and code != current_language():
            set_language(code)
            self.language_hint.setText(tr("Dil değişikliğinin uygulanması için programı yeniden başlat."))
            self.language_hint.setStyleSheet(f"color: {theme.ACCENT_DARK}; font-weight: 600;")
