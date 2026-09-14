"""5 · Çeviri ilerlemesi: blok ve aşama görünür, durdurulabilir (talimat 4.3, 4.4)."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from app.core.history import format_duration
from app.core.i18n import tr
from app.ui import theme
from app.ui.widgets import Card, Pill, StatTile, label, svg_icon
from PySide6.QtWidgets import QLabel


class BlockStrip(QWidget):
    """Blok başına bir dilim: bitti (mavi), sürüyor (yarı), bekliyor (gri)."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.lay = QHBoxLayout(self); self.lay.setContentsMargins(0, 0, 0, 0); self.lay.setSpacing(4)
        self.setFixedHeight(10)

    def set_state(self, total: int, done: int, current_fraction: float = 0.0) -> None:
        while self.lay.count():
            w = self.lay.takeAt(0).widget()
            if w:
                w.deleteLater()
        for i in range(max(total, 1)):
            seg = QFrame(); seg.setFixedHeight(10)
            if i < done:
                seg.setStyleSheet(f"background: {theme.ACCENT}; border-radius: 3px;")
            elif i == done and total > done:
                pct = int(max(0.0, min(1.0, current_fraction)) * 100)
                seg.setStyleSheet(
                    f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:{pct/100:.2f} {theme.ACCENT}, "
                    f"stop:{min(1.0, pct/100 + 0.001):.3f} #cfe0ee); border-radius: 3px;")
            else:
                seg.setStyleSheet(f"background: {theme.BORDER}; border-radius: 3px;")
            self.lay.addWidget(seg, 1)


class GpuPanel(QWidget):
    """Sıcaklık, kullanım, VRAM; her biri çubukla. GPU yoksa gizli."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(12)
        self.card = Card(padding=16, spacing=12)
        cap = QVBoxLayout(); cap.setSpacing(2)
        c = label(tr("EKRAN KARTI"), "TileLabel"); c.setStyleSheet("letter-spacing: 1px; font-size: 8.5pt;")
        self.name = label("—", "SectionTitle"); self.name.setStyleSheet("font-size: 9.5pt;"); self.name.setWordWrap(True)
        cap.addWidget(c); cap.addWidget(self.name); self.card.body.addLayout(cap)
        self.rows = {}
        for key, title in (("temp", tr("Sıcaklık")), ("util", tr("Kullanım")), ("mem", tr("Bellek (VRAM)"))):
            box = QVBoxLayout(); box.setSpacing(4)
            top = QHBoxLayout(); top.addWidget(label(title, "TileLabel")); top.addStretch()
            val = label("—", "SectionTitle"); val.setStyleSheet("font-size: 11pt;"); top.addWidget(val)
            bar = QFrame(); bar.setFixedHeight(6); bar.setStyleSheet(f"background: {theme.BORDER}; border-radius: 3px;")
            fill = QFrame(bar); fill.setGeometry(0, 0, 0, 6); fill.setStyleSheet(f"background: {theme.ACCENT}; border-radius: 3px;")
            box.addLayout(top); box.addWidget(bar)
            self.card.body.addLayout(box)
            self.rows[key] = (val, bar, fill)
        self.card.body.addWidget(label(tr("2 sn'de bir güncellenir"), "TileLabel"))
        outer.addWidget(self.card)

        self.queue_card = Card(padding=16, spacing=8)
        qc = label(tr("SIRA"), "TileLabel"); qc.setStyleSheet("letter-spacing: 1px; font-size: 8.5pt;")
        self.queue_card.body.addWidget(qc)
        self.queue_box = QVBoxLayout(); self.queue_box.setSpacing(6); self.queue_card.body.addLayout(self.queue_box)
        outer.addWidget(self.queue_card)
        outer.addStretch()

    def _set(self, key: str, text: str, frac: float, color: str = theme.ACCENT) -> None:
        val, bar, fill = self.rows[key]
        val.setText(text)
        w = int(max(0.0, min(1.0, frac)) * bar.width())
        fill.setGeometry(0, 0, w, 6); fill.setStyleSheet(f"background: {color}; border-radius: 3px;")

    def update_sample(self, s) -> None:
        self.card.show()
        self.name.setText(s.name)
        if s.temp_c is not None:
            col = theme.DANGER if s.temp_c >= 85 else ("#d97706" if s.temp_c >= 70 else theme.ACCENT)
            self._set("temp", f"{s.temp_c} °C", s.temp_c / 100, col)
        if s.util_pct is not None:
            self._set("util", f"{s.util_pct} %", s.util_pct / 100)
        if s.mem_used_mb is not None and s.mem_total_mb:
            self._set("mem", f"{s.mem_used_mb / 1024:.1f} / {s.mem_total_mb / 1024:.0f} GB".replace(".", ","), s.mem_used_mb / s.mem_total_mb)

    def set_gpu_available(self, ok: bool) -> None:
        self.card.setVisible(ok)

    def set_queue(self, names: list[str], current: int) -> None:
        while self.queue_box.count():
            w = self.queue_box.takeAt(0).widget()
            if w:
                w.deleteLater()
        for i, n in enumerate(names):
            row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(8)
            num = QLabel(str(i + 1)); num.setFixedSize(18, 18); num.setAlignment(Qt.AlignCenter)
            active = i == current
            num.setStyleSheet(f"border-radius: 9px; font-size: 8pt; font-weight: 600; background: {theme.ACCENT if active else theme.BORDER}; color: {'#fff' if active else theme.TEXT_SOFT};")
            t = label(n, None if active else "Subtle"); t.setStyleSheet("font-weight: 600;" if active else "")
            fm = t.fontMetrics(); t.setText(fm.elidedText(n, Qt.ElideRight, 150))
            if i < current:
                t.setStyleSheet(f"color: {theme.SUCCESS};")
            h.addWidget(num); h.addWidget(t, 1)
            self.queue_box.addWidget(row)
        self.queue_card.setVisible(len(names) > 1)


class ConvertPage(QWidget):
    stop_requested = Signal()
    skip_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        outer = QHBoxLayout(self); outer.setContentsMargins(28, 24, 28, 24); outer.setSpacing(20)
        leftw = QWidget(); root = QVBoxLayout(leftw); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(18)
        outer.addWidget(leftw, 1)
        self.gpu = GpuPanel(); outer.addWidget(self.gpu)

        head = QHBoxLayout(); head.setSpacing(16)
        col = QVBoxLayout(); col.setSpacing(4)
        self.counter = label("", "Subtle")
        self.title = label(tr("… dönüştürülüyor"), "H2", wrap=True)
        self.meta = label("", "Subtle", wrap=True)
        col.addWidget(self.counter); col.addWidget(self.title); col.addWidget(self.meta)
        head.addLayout(col, 1)
        self.stage_pill = Pill(tr("Aşama 1 / 2: OCR"), "accent"); head.addWidget(self.stage_pill, 0, Qt.AlignTop)
        root.addLayout(head)

        pc = Card(spacing=14)
        top = QHBoxLayout()
        self.block_label = label(tr("Blok — / —"), "SectionTitle"); top.addWidget(self.block_label); top.addStretch()
        self.percent = label("0 %", "BigPercent"); top.addWidget(self.percent)
        pc.body.addLayout(top)
        self.strip = BlockStrip(); pc.body.addWidget(self.strip)
        grid = QGridLayout(); grid.setSpacing(12)
        self.tile_elapsed = StatTile(tr("Geçen süre"), tr("0 sn")); self.tile_eta = StatTile(tr("Bu kitap için kalan"), "—"); self.tile_avg = StatTile(tr("Sıradaki kitaplar"), "—")
        grid.addWidget(self.tile_elapsed, 0, 0); grid.addWidget(self.tile_eta, 0, 1); grid.addWidget(self.tile_avg, 0, 2)
        pc.body.addLayout(grid)
        root.addWidget(pc)

        lc = Card(padding=16, spacing=10)
        lc.body.addWidget(label(tr("Şu an"), "SectionTitle"))
        self.log_box = QVBoxLayout(); self.log_box.setSpacing(6)
        lc.body.addLayout(self.log_box)
        root.addWidget(lc)

        self.next_label = label("", "Subtle", wrap=True)
        root.addWidget(self.next_label)
        root.addStretch()

        bottom = QHBoxLayout(); bottom.setSpacing(8)
        bottom.addWidget(label(tr("Durdurursan biten bloklar saklanır. Bilgisayar bu sırada uyumaz."), "Subtle", wrap=True), 1)
        self.skip = QPushButton(tr("Bu kitabı atla")); self.skip.setMinimumHeight(44); self.skip.clicked.connect(self.skip_requested)
        self.stop = QPushButton("  " + tr("Durdur")); self.stop.setObjectName("Danger"); self.stop.setIcon(svg_icon("stop", theme.DANGER, 14))
        self.stop.clicked.connect(self.stop_requested)
        bottom.addWidget(self.skip); bottom.addWidget(self.stop)
        root.addLayout(bottom)
        self._log_lines: list[tuple[str, str]] = []

    def begin(self, pdf_name: str, force_ocr: bool, gpu_name: str, total_blocks: int, done_blocks: int, has_outline: bool | None,
              index: int = 0, total_books: int = 1, is_test: bool = False) -> None:
        self.counter.setText(tr("Kitap {i} / {n}", i=index + 1, n=total_books) if total_books > 1 else "")
        self.title.setText(f"{pdf_name} " + (tr("test ediliyor") if is_test else tr("dönüştürülüyor")))
        now = datetime.now().strftime("%H:%M")
        self.meta.setText(tr("Başladı {now} · Zorunlu OCR {state}", now=now, state=(tr("açık") if force_ocr else tr("kapalı")))
                          + (f" · {gpu_name}" if gpu_name else ""))
        self.skip.setVisible(total_books > 1)
        self.set_stage(1)
        self.update_blocks(total_blocks, done_blocks, 0.0, None, None)
        self._log_lines.clear(); self._render_log()
        if has_outline is None:
            self.next_label.setText(tr("Sırada: Aşama 2 / 2 Bölme."))
        elif has_outline:
            self.next_label.setText(tr("Sırada: Aşama 2 / 2 Bölme. İçindekiler bulundu, gerçek bölümlere ayrılacak."))
        else:
            self.next_label.setText(tr("Sırada: Aşama 2 / 2 Bölme. İçindekiler yok, 40 sayfalık parçalara ayrılacak."))
        self.stop.setEnabled(True); self.stop.setText("  " + tr("Durdur"))

    def set_stage(self, stage: int) -> None:
        self.stage_pill.setText(tr("Aşama 1 / 2: OCR") if stage == 1 else tr("Aşama 2 / 2: Bölme"))

    def update_blocks(self, total: int, done: int, current_fraction: float, page_from: int | None, page_to: int | None) -> None:
        cur = min(done + 1, total) if total else 0
        pages = tr(" · sayfalar {a}–{b}", a=page_from, b=page_to) if page_from and page_to else ""
        self.block_label.setText(tr("Blok {cur} / {total}", cur=cur, total=total) + pages)
        frac = (done + current_fraction) / total if total else 0.0
        self.percent.setText(f"{int(frac * 100)} %")
        self.strip.set_state(total, done, current_fraction)

    def update_times(self, elapsed_sec: float, eta_sec: float | None, remaining_books: int, remaining_eta: float | None) -> None:
        self.tile_elapsed.set_value(format_duration(elapsed_sec))
        self.tile_eta.set_value(f"~ {format_duration(eta_sec)}" if eta_sec else tr("hesaplanıyor…"))
        if remaining_books:
            self.tile_avg.set_value(f"{remaining_books}" + (f" · ~ {format_duration(remaining_eta)}" if remaining_eta else ""))
        else:
            self.tile_avg.set_value(tr("yok"))

    def add_log(self, text: str) -> None:
        self._log_lines.insert(0, (datetime.now().strftime("%H:%M"), text))
        del self._log_lines[3:]
        self._render_log()

    def _render_log(self) -> None:
        while self.log_box.count():
            w = self.log_box.takeAt(0).widget()
            if w:
                w.deleteLater()
        for t, msg in self._log_lines:
            row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(12)
            tl = label(t, "Subtle"); tl.setFixedWidth(44); tl.setStyleSheet("color: #9ca3af;")
            h.addWidget(tl); h.addWidget(label(msg, "Soft", wrap=True), 1)
            self.log_box.addWidget(row)
        if not self._log_lines:
            self.log_box.addWidget(label(tr("Hazırlanıyor…"), "Subtle"))

    def set_stopping(self) -> None:
        self.stop.setEnabled(False); self.stop.setText("  " + tr("Durduruluyor…")); self.skip.setEnabled(False)
