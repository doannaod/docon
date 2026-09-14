"""7 · Geçmiş işler: liste, arama, seçili iş ayrıntısı (talimat 4.6)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from app.core.history import JobRecord
from app.core.i18n import tr
from app.core.paths import format_bytes, open_in_explorer
from app.ui.widgets import Card, Pill, label, svg_icon

COL_RATIO = (0.26, 0.13, 0.12, 0.19, 0.14, 0.16)


def _cols() -> list[str]:
    return [tr("Kitap"), tr("Tarih"), tr("Süre"), tr("PDF → Çıktı"), tr("Kaydedildiği yer"), tr("Durum")]


class RatioTable(QTableWidget):
    """Sütunları genişliğe orantılı dağıtan tablo."""

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        total = self.viewport().width()
        for i, r in enumerate(COL_RATIO):
            self.setColumnWidth(i, int(total * r))


class HistoryPage(QWidget):
    resume_requested = Signal(str)
    open_log_requested = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._jobs: list[JobRecord] = []
        self._selected: JobRecord | None = None
        root = QVBoxLayout(self); root.setContentsMargins(36, 28, 36, 28); root.setSpacing(20)

        head = QHBoxLayout(); head.setSpacing(16)
        col = QVBoxLayout(); col.setSpacing(4)
        col.addWidget(label(tr("Geçmiş İşler"), "H2"))
        self.summary = label("", "Subtle"); col.addWidget(self.summary)
        head.addLayout(col, 1)
        self.search = QLineEdit(); self.search.setPlaceholderText(tr("Kitap adında ara")); self.search.setFixedWidth(260)
        self.search.addAction(svg_icon("search", "#9ca3af", 16), QLineEdit.LeadingPosition)
        self.search.textChanged.connect(self._refresh)
        head.addWidget(self.search, 0, Qt.AlignTop)
        root.addLayout(head)

        cols = _cols()
        self.table = RatioTable(0, len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.verticalHeader().hide()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setShowGrid(False)
        self.table.setAlternatingRowColors(False)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        hh = self.table.horizontalHeader()
        hh.setStretchLastSection(False)
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table, 1)

        self.detail = Card(padding=16, spacing=10)
        dh = QHBoxLayout()
        self.detail_title = label(tr("Bir iş seç"), "SectionTitle"); dh.addWidget(self.detail_title, 1)
        self.btn_log = QPushButton(tr("Ayrıntılı günlük")); self.btn_log.setObjectName("Small")
        self.btn_log.clicked.connect(lambda: self._selected and self.open_log_requested.emit(self._selected.id))
        self.btn_resume = QPushButton(tr("Kaldığı yerden devam et")); self.btn_resume.setObjectName("Small")
        self.btn_resume.clicked.connect(lambda: self._selected and self.resume_requested.emit(self._selected.id))
        self.btn_open = QPushButton(tr("Klasöre Git")); self.btn_open.setObjectName("SmallPrimary")
        self.btn_open.clicked.connect(self._open_folder)
        dh.addWidget(self.btn_log); dh.addWidget(self.btn_resume); dh.addWidget(self.btn_open)
        self.detail.body.addLayout(dh)
        self.detail_text = label("", "Subtle", wrap=True); self.detail.body.addWidget(self.detail_text)
        root.addWidget(self.detail)
        self._set_detail(None)

    def set_jobs(self, jobs: list[JobRecord]) -> None:
        self._jobs = jobs
        done = sum(1 for j in jobs if j.status == "done")
        half = sum(1 for j in jobs if j.status in ("paused", "running"))
        self.summary.setText(tr("Bugüne kadar dönüştürülen {done} kitap, {half} yarım kalan iş", done=done, half=half))
        self._refresh()

    def _refresh(self) -> None:
        q = self.search.text().strip().lower()
        rows = [j for j in self._jobs if q in j.pdf_name.lower()]
        self.table.setRowCount(0)
        for j in rows:
            r = self.table.rowCount(); self.table.insertRow(r)
            name = QTableWidgetItem(j.pdf_name); name.setData(Qt.UserRole, j.id)
            f = name.font(); f.setBold(True); name.setFont(f)
            self.table.setItem(r, 0, name)
            self.table.setItem(r, 1, QTableWidgetItem(j.date_label))
            self.table.setItem(r, 2, QTableWidgetItem(j.duration_label if j.duration_sec else "—"))
            out = format_bytes(j.output_bytes) if j.output_bytes else "—"
            self.table.setItem(r, 3, QTableWidgetItem(f"{format_bytes(j.input_bytes)} → {out}"))
            self.table.setItem(r, 4, QTableWidgetItem(j.output_dir))
            pill = Pill(j.status_label, "success" if j.status == "done" else ("warn" if j.status in ("paused", "running") else "warn"))
            pill.setStyleSheet("padding: 3px 8px; font-size: 8.5pt;")
            holder = QWidget(); hl = QHBoxLayout(holder); hl.setContentsMargins(4, 4, 8, 4); hl.addStretch(); hl.addWidget(pill)
            self.table.setCellWidget(r, 5, holder)
            self.table.setRowHeight(r, 44)
        self._set_detail(None)

    def _on_select(self) -> None:
        items = self.table.selectedItems()
        if not items:
            self._set_detail(None); return
        job_id = self.table.item(items[0].row(), 0).data(Qt.UserRole)
        self._set_detail(next((j for j in self._jobs if j.id == job_id), None))

    def _set_detail(self, job: JobRecord | None) -> None:
        self._selected = job
        has = job is not None
        for b in (self.btn_log, self.btn_open):
            b.setEnabled(has)
        self.btn_resume.setVisible(has and job.status in ("paused", "running"))
        if not has:
            self.detail_title.setText(tr("Bir iş seç")); self.detail_text.setText(tr("Ayrıntıları görmek için listeden bir kitap seç.")); return
        self.detail_title.setText(tr("Seçili: {name}", name=job.pdf_name))
        parts = [tr("{n} sayfa", n=f"{job.page_count:,}".replace(",", ".")),
                 tr("{n} blok", n=job.total_blocks) if job.total_blocks else None,
                 tr("Zorunlu OCR {state}", state=(tr("açık") if job.force_ocr else tr("kapalı"))),
                 tr("{ch} bölüm, {ek} ek", ch=job.chapters, ek=job.appendices) if job.chapters else None,
                 tr("{n} şekil", n=job.figures) if job.figures else None,
                 f"{job.date_label} {job.started_at[11:16]}" + (f" – {job.finished_at[11:16]}" if job.finished_at else ""),
                 job.message or None]
        self.detail_text.setText(" · ".join(p for p in parts if p))

    def _open_folder(self) -> None:
        if self._selected and Path(self._selected.output_dir).exists():
            open_in_explorer(Path(self._selected.output_dir))
