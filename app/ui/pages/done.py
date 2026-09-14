"""6 · Bitti: boyutlar, üretilen dosyalar, Klasöre Git (talimat 4.5, 4.7)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.core.history import JobRecord, format_duration
from app.core.i18n import tr
from app.core.paths import format_bytes, open_in_explorer
from app.ui import theme
from app.ui.widgets import Card, StatTile, icon_label, label, scroll_body, svg_icon


class DonePage(QWidget):
    new_book = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._output: Path | None = None
        root = scroll_body(self, spacing=20)

        head = QHBoxLayout(); head.setSpacing(14)
        badge = QWidget(); badge.setFixedSize(44, 44)
        badge.setStyleSheet(f"background: {theme.SUCCESS_SOFT}; border-radius: 22px;")
        bl = QHBoxLayout(badge); bl.setContentsMargins(0, 0, 0, 0)
        bl.addWidget(icon_label("check", theme.SUCCESS, 24, 2.5), 0, Qt.AlignCenter)
        head.addWidget(badge, 0, Qt.AlignTop)
        col = QVBoxLayout(); col.setSpacing(4)
        self.title = label(tr("… hazır"), "H2", wrap=True); self.meta = label("", "Subtle", wrap=True)
        col.addWidget(self.title); col.addWidget(self.meta)
        head.addLayout(col, 1)
        root.addLayout(head)

        grid = QGridLayout(); grid.setSpacing(12)
        self.t_in = StatTile(tr("Yüklenen PDF"), card=True); self.t_out = StatTile(tr("Çıktı klasörü"), card=True)
        self.t_ch = StatTile(tr("Bölüm dosyası"), card=True); self.t_fig = StatTile(tr("Şekil ve grafik"), card=True)
        for i, t in enumerate((self.t_in, self.t_out, self.t_ch, self.t_fig)):
            grid.addWidget(t, 0, i)
        root.addLayout(grid)

        fc = Card()
        fh = QHBoxLayout(); fh.addWidget(label(tr("Üretilen dosyalar"), "SectionTitle")); fh.addStretch()
        self.out_path = label("", "TileLabel"); fh.addWidget(self.out_path)
        fc.body.addLayout(fh)
        self.quality = label("", "Soft", wrap=True); fc.body.addWidget(self.quality)
        self.files_grid = QGridLayout(); self.files_grid.setHorizontalSpacing(24); self.files_grid.setVerticalSpacing(6)
        fc.body.addLayout(self.files_grid)
        root.addWidget(fc)
        root.addStretch()

        actions = QHBoxLayout(); actions.addStretch(); actions.setSpacing(10)
        nb = QPushButton(tr("Yeni Kitap Ekle")); nb.setMinimumHeight(44); nb.clicked.connect(self.new_book)
        go = QPushButton("  " + tr("Klasöre Git")); go.setObjectName("Primary"); go.setIcon(svg_icon("folder", "#ffffff", 16))
        go.clicked.connect(self._open)
        actions.addWidget(nb); actions.addWidget(go)
        root.addLayout(actions)

    def show_job(self, job: JobRecord, others_done: int = 0) -> None:
        self._output = Path(job.output_dir)
        self.title.setText(tr("{name} hazır", name=job.display_name) +
                           (tr(" · toplam {n} kitap bitti", n=others_done + 1) if others_done else ""))
        fin = job.finished_at[11:16] if job.finished_at else ""
        self.meta.setText(tr("Tamamlandı {t} · Toplam süre {sure} · Zorunlu OCR {state}",
                             t=fin, sure=format_duration(job.duration_sec),
                             state=(tr("açık") if job.force_ocr else tr("kapalı"))))
        self.quality.setText(tr("Kalite taraması: {q}", q=job.quality) if job.quality else "")
        self.quality.setVisible(bool(job.quality))
        self.t_in.set_value(format_bytes(job.input_bytes)); self.t_out.set_value(format_bytes(job.output_bytes))
        self.t_ch.set_value(tr("{n} + {ek} ek", n=job.chapters, ek=job.appendices) if job.appendices else str(job.chapters))
        self.t_fig.set_value(str(job.figures))
        self.out_path.setText(job.output_dir)
        self.out_path.setToolTip(job.output_dir)
        fm = self.out_path.fontMetrics()
        self.out_path.setText(fm.elidedText(job.output_dir, Qt.ElideMiddle, 420))
        self._fill_files()

    def _fill_files(self) -> None:
        while self.files_grid.count():
            w = self.files_grid.takeAt(0).widget()
            if w:
                w.deleteLater()
        if not self._output or not self._output.exists():
            self.files_grid.addWidget(label(tr("Çıktı klasörü bulunamadı. Taşınmış ya da silinmiş olabilir."), "Subtle", wrap=True), 0, 0, 1, 2)
            return
        entries: list[str] = []
        md = sorted(p.name for p in self._output.glob("*.md"))
        if "00-index.md" in md:
            entries.append(tr("00-index.md · birimler, alt kısımlar, tablo ve şekil listesi")); md.remove("00-index.md")
        if "birlesik.md" in md:
            entries.append(tr("birlesik.md · kitabın tamamı tek dosyada")); md.remove("birlesik.md")
        chapters = [m for m in md if m.startswith(("bolum-", "kisim-"))]
        others = [m for m in md if m not in chapters]
        entries += others
        if chapters:
            entries.append(chapters[0] if len(chapters) == 1 else f"{chapters[0]} … {chapters[-1]}")
        figs = self._output / "sekiller"
        if figs.exists():
            n = sum(1 for p in figs.rglob("*") if p.is_file())
            entries.append(tr("sekiller\\ · {n} görsel", n=n))
        for i, e in enumerate(entries):
            self.files_grid.addWidget(label(e, "Soft", wrap=True), i // 2, i % 2)

    def _open(self) -> None:
        if self._output and self._output.exists():
            open_in_explorer(self._output)
