"""4 · İlk kurulum: yazılım ve modeller iniyor (talimat 3.8, 4.0–4.2, zorluk 5.1)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QVBoxLayout, QWidget,
)

from app.core.i18n import tr
from app.core.paths import format_bytes
from app.ui import theme
from app.ui.widgets import Card, StatTile, icon_label, label


@dataclass
class SetupStep:
    key: str
    title: str
    total_bytes: int = 0
    done_bytes: int = 0
    state: str = "pending"   # pending | running | done | error


class _StepRow(QWidget):
    def __init__(self, step: SetupStep, last: bool):
        super().__init__()
        lay = QHBoxLayout(self); lay.setContentsMargins(16, 12, 16, 12); lay.setSpacing(12)
        self.icon_slot = QHBoxLayout(); self.icon_slot.setContentsMargins(0, 0, 0, 0)
        holder = QWidget(); holder.setFixedWidth(16); holder.setLayout(self.icon_slot)
        lay.addWidget(holder)
        self.title = label(step.title); lay.addWidget(self.title, 1)
        self.size = label("", "Subtle"); lay.addWidget(self.size)
        self.state = label("", "Subtle"); self.state.setFixedWidth(110); self.state.setAlignment(Qt.AlignRight)
        lay.addWidget(self.state)
        if not last:
            self.setStyleSheet("border-bottom: 1px solid #eef0f2;")
        self.update_from(step)

    def update_from(self, s: SetupStep) -> None:
        while self.icon_slot.count():
            w = self.icon_slot.takeAt(0).widget()
            if w:
                w.deleteLater()
        if s.state == "done":
            self.icon_slot.addWidget(icon_label("check", theme.SUCCESS, 16, 2.5))
            self.state.setText(tr("Tamamlandı")); self.state.setStyleSheet(f"color: {theme.SUCCESS};")
            self.size.setText(format_bytes(s.total_bytes) if s.total_bytes else "")
        elif s.state == "running":
            self.icon_slot.addWidget(icon_label("download", theme.ACCENT, 16, 2.5))
            self.state.setText(tr("İniyor…")); self.state.setStyleSheet(f"color: {theme.ACCENT};")
            self.size.setText(f"{format_bytes(s.done_bytes)} / {format_bytes(s.total_bytes)}" if s.total_bytes else "")
        elif s.state == "error":
            self.state.setText(tr("Hata")); self.state.setStyleSheet(f"color: {theme.DANGER};")
        else:
            self.state.setText(tr("Bekliyor")); self.state.setStyleSheet(f"color: {theme.TEXT_MUTED};")
            self.size.setText("")


class SetupPage(QWidget):
    pause_requested = Signal()
    resume_requested = Signal()
    retry_requested = Signal()
    start_requested = Signal()     # onay: "İndirmeyi başlat"
    later_requested = Signal()     # "Sonra"

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._rows: dict[str, _StepRow] = {}
        root = QVBoxLayout(self); root.setContentsMargins(36, 28, 36, 28); root.setSpacing(20)

        head = QVBoxLayout(); head.setSpacing(6)
        self.heading = label(tr("Hoş geldin. Program ilk kez açılıyor."), "H2", wrap=True)
        head.addWidget(self.heading)
        self.subtitle = label(tr("Kitap çevirmeye başlamadan önce bir kerelik hazırlık gerekiyor. Bu ekran yalnızca ilk açılışta görünür."), "Subtle", wrap=True)
        head.addWidget(self.subtitle)
        root.addLayout(head)

        # --- ONAY KARTI (kurulum başlamadan önce) ---
        self.consent = Card(spacing=14)
        crow = QHBoxLayout(); crow.setSpacing(14)
        crow.addWidget(icon_label("download", theme.ACCENT, 28, 1.8), 0, Qt.AlignTop)
        ccol = QVBoxLayout(); ccol.setSpacing(8)
        self.consent_title = label(tr("Yaklaşık {gb} GB indirilecek. Başlayalım mı?", gb="7,4"), "SectionTitle"); self.consent_title.setStyleSheet("font-size: 12pt;")
        why = label(tr("<b>Neden gerekli:</b> PDF sayfalarını okuyup Markdown'a çeviren yapay zekâ modelleri (surya) ve onları ekran "
                    "kartında çalıştıran yazılım (torch, marker) programın içinde gelmiyor; boyutları yüzünden bir kez internetten "
                    "indirilir ve bilgisayarında kalır. Sonraki açılışlarda tekrar inmez."), "Soft", wrap=True)
        why.setTextFormat(Qt.RichText)
        how = label(tr("Terminal açmana veya elle bir şey kurmana gerek yok. Bağlantı koparsa indirme kaldığı yerden devam eder. "
                    "İndirme bitince bildirim alırsın; sonra istediğin zaman kitap ekleyip çevirebilirsin."), "Soft", wrap=True)
        ccol.addWidget(self.consent_title); ccol.addWidget(why); ccol.addWidget(how)
        crow.addLayout(ccol, 1)
        self.consent.body.addLayout(crow)
        self.consent_check = QFrame(); self.consent_check.setObjectName("InfoBanner")
        ckl = QHBoxLayout(self.consent_check); ckl.setContentsMargins(10, 8, 10, 8)
        self.consent_check_text = label("", "InfoText", wrap=True); self.consent_check_text.setStyleSheet("font-size: 9pt;")
        ckl.addWidget(self.consent_check_text)
        self.consent.body.addWidget(self.consent_check)
        cact = QHBoxLayout(); cact.addStretch(); cact.setSpacing(10)
        self.later = QPushButton(tr("Sonra (programı gez)")); self.later.clicked.connect(self.later_requested)
        self.start = QPushButton(tr("İndirmeyi başlat")); self.start.setObjectName("Primary"); self.start.clicked.connect(self.start_requested)
        cact.addWidget(self.later); cact.addWidget(self.start)
        self.consent.body.addLayout(cact)
        root.addWidget(self.consent)

        pc = Card(spacing=14); self.progress_card = pc
        top = QHBoxLayout(); top.addWidget(label(tr("Toplam ilerleme"), "SectionTitle")); top.addStretch()
        self.percent = label("0 %", "BigPercent"); top.addWidget(self.percent)
        pc.body.addLayout(top)
        self.bar = QProgressBar(); self.bar.setRange(0, 1000); self.bar.setTextVisible(False)
        pc.body.addWidget(self.bar)
        grid = QGridLayout(); grid.setSpacing(12)
        self.tile_speed = StatTile(tr("İnternet hızı"), "—"); self.tile_eta = StatTile(tr("Tahmini kalan süre"), "—"); self.tile_bytes = StatTile(tr("İnen / toplam"), "—")
        grid.addWidget(self.tile_speed, 0, 0); grid.addWidget(self.tile_eta, 0, 1); grid.addWidget(self.tile_bytes, 0, 2)
        pc.body.addLayout(grid)
        root.addWidget(pc)

        self.steps_card = Card(padding=0, spacing=0)
        root.addWidget(self.steps_card)

        self.banner = QFrame(); self.banner.setObjectName("InfoBanner")
        bl = QHBoxLayout(self.banner); bl.setContentsMargins(16, 12, 16, 12); bl.setSpacing(10)
        bl.addWidget(icon_label("info", theme.ACCENT_DARK, 16), 0, Qt.AlignTop)
        self.banner_text = label(tr("Bağlantı koparsa indirme kaldığı yerden devam eder."), "InfoText", wrap=True)
        bl.addWidget(self.banner_text, 1)
        root.addWidget(self.banner)

        root.addStretch()
        actions = QHBoxLayout(); actions.addStretch(); actions.setSpacing(10)
        self.retry = QPushButton(tr("Yeniden dene")); self.retry.setObjectName("Primary"); self.retry.hide()
        self.retry.clicked.connect(self.retry_requested)
        self.pause = QPushButton(tr("Duraklat")); self.pause.setMinimumHeight(44); self.pause.setCheckable(True)
        self.pause.toggled.connect(self._toggle_pause)
        actions.addWidget(self.retry); actions.addWidget(self.pause)
        root.addLayout(actions)

    def show_consent(self, check_text: str, total_gb: float) -> None:
        """Kurulum öncesi onay durumu."""
        self.heading.setText(tr("Hoş geldin. Program ilk kez açılıyor."))
        self.subtitle.setText(tr("Kitap çevirmeye başlamadan önce bir kerelik hazırlık gerekiyor. Bu ekran yalnızca ilk açılışta görünür."))
        gb = f"{total_gb:.1f}".replace(".", ",")
        self.consent_title.setText(tr("Yaklaşık {gb} GB indirilecek. Başlayalım mı?", gb=gb))
        self.consent_check_text.setText(check_text)
        self.consent.show(); self.progress_card.hide(); self.banner.hide(); self.pause.hide(); self.retry.hide()
        self.steps_card.setStyleSheet("QFrame#Card { background: #ffffff; }"); self.steps_card.setGraphicsEffect(None)

    def show_progress(self) -> None:
        """İndirme sürüyor durumu."""
        self.heading.setText(tr("İlk kurulum: gereken yazılım ve modeller iniyor"))
        self.subtitle.setText(tr("Bu işlem yalnızca bir kez yapılır. Bittiğinde bildirim alırsın; kitap çevirmeye o zaman başlarsın."))
        self.consent.hide(); self.progress_card.show(); self.banner.show(); self.pause.show()
        self.pause.blockSignals(True); self.pause.setChecked(False); self.pause.setText(tr("Duraklat")); self.pause.blockSignals(False)

    def set_steps(self, steps: list[SetupStep]) -> None:
        while self.steps_card.body.count():
            w = self.steps_card.body.takeAt(0).widget()
            if w:
                w.deleteLater()
        self._rows.clear()
        for i, s in enumerate(steps):
            row = _StepRow(s, last=(i == len(steps) - 1))
            self._rows[s.key] = row
            self.steps_card.body.addWidget(row)

    def update_step(self, step: SetupStep) -> None:
        if step.key in self._rows:
            self._rows[step.key].update_from(step)

    def update_progress(self, fraction: float, speed_bps: float | None, eta_sec: float | None,
                        done_bytes: int, total_bytes: int) -> None:
        self.bar.setValue(int(max(0.0, min(1.0, fraction)) * 1000))
        self.percent.setText(f"{int(fraction * 100)} %")
        self.tile_speed.set_value(f"{format_bytes(speed_bps)}/s" if speed_bps else "—")
        if eta_sec is None:
            self.tile_eta.set_value(tr("hesaplanıyor…"))
        else:
            m, s = divmod(int(eta_sec), 60)
            h, m = divmod(m, 60)
            self.tile_eta.set_value(tr("{h} sa {m} dk", h=h, m=m) if h else tr("{m} dk {s} sn", m=m, s=f"{s:02d}"))
        self.tile_bytes.set_value(f"{format_bytes(done_bytes)} / {format_bytes(total_bytes)}" if total_bytes else "—")

    def set_banner(self, text: str, error: bool = False) -> None:
        self.banner_text.setText(text)
        self.banner_text.setStyleSheet(f"color: {theme.DANGER};" if error else "")
        self.retry.setVisible(error)

    def _toggle_pause(self, paused: bool) -> None:
        self.pause.setText(tr("Devam et") if paused else tr("Duraklat"))
        (self.pause_requested if paused else self.resume_requested).emit()
