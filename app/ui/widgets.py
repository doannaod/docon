"""Tasarımda tekrar eden küçük bileşenler: kart, istatistik kutusu, etiket, ikon."""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QSize, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

# --- ikonlar (tasarımdaki inline SVG'ler, çizgi tabanlı) ---
_ICONS = {
    "file": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/>',
    "file-up": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6"/><path d="M12 18v-6M9 15l3-3 3 3"/>',
    "home": '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "check": '<path d="M5 12l5 5L20 7"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "play": '<path d="M7 5v14l11-7z" fill="currentColor" stroke="none"/>',
    "stop": '<rect x="5" y="5" width="14" height="14" rx="2" fill="currentColor" stroke="none"/>',
    "download": '<path d="M12 3v12M7 10l5 5 5-5"/><path d="M4 20h16"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/>',
    "shield": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    "grip": '<circle cx="9" cy="6" r="1.4" fill="currentColor" stroke="none"/><circle cx="15" cy="6" r="1.4" fill="currentColor" stroke="none"/><circle cx="9" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="15" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="9" cy="18" r="1.4" fill="currentColor" stroke="none"/><circle cx="15" cy="18" r="1.4" fill="currentColor" stroke="none"/>',
    "skip": '<path d="M5 5l9 7-9 7z" fill="currentColor" stroke="none"/><rect x="16" y="5" width="3" height="14" rx="1" fill="currentColor" stroke="none"/>',
    "thermo": '<path d="M14 14.8V5a2 2 0 1 0-4 0v9.8a4 4 0 1 0 4 0z"/>',
}


def svg_icon(name: str, color: str = "#1c1f23", size: int = 18, stroke: float = 2.0) -> QIcon:
    body = _ICONS[name].replace("currentColor", color)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pix = QPixmap(size, size)
    pix.fill(Qt.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)


def icon_label(name: str, color: str, size: int = 18, stroke: float = 2.0) -> QLabel:
    lbl = QLabel()
    lbl.setPixmap(svg_icon(name, color, size, stroke).pixmap(QSize(size, size)))
    lbl.setFixedSize(size, size)
    return lbl


def label(text: str, object_name: str | None = None, wrap: bool = False) -> QLabel:
    lbl = QLabel(text)
    if object_name:
        lbl.setObjectName(object_name)
    lbl.setWordWrap(wrap)
    return lbl


class Card(QFrame):
    """Beyaz, ince kenarlıklı kart. Dikey yerleşim, 20px iç boşluk."""

    def __init__(self, padding: int = 20, spacing: int = 12, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(padding, padding, padding, padding)
        self.body.setSpacing(spacing)


class StatTile(QFrame):
    """Küçük başlık + kalın değer kutusu (gri zemin, kart içinde) ya da beyaz kart (StatCard)."""

    def __init__(self, title: str, value: str = "—", card: bool = False, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("StatCard" if card else "StatTile")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(4)
        self.title = label(title, "TileLabel")
        self.value = label(value, "TileValue")
        lay.addWidget(self.title)
        lay.addWidget(self.value)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_value(self, text: str) -> None:
        self.value.setText(text)


class Pill(QLabel):
    """Yuvarlak durum etiketi: kind = success | warn | accent"""

    def __init__(self, text: str, kind: str = "accent", parent: QWidget | None = None):
        super().__init__(text, parent)
        self.setObjectName("Pill")
        self.set_kind(kind)
        self.setAlignment(Qt.AlignCenter)

    def set_kind(self, kind: str) -> None:
        self.setProperty("kind", kind)
        self.style().unpolish(self)
        self.style().polish(self)


class Spacer(QWidget):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)


def hbox(*widgets: QWidget, spacing: int = 12, stretch_last: bool = False) -> QHBoxLayout:
    lay = QHBoxLayout()
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(spacing)
    for w in widgets:
        lay.addWidget(w)
    if stretch_last:
        lay.addStretch()
    return lay


def scroll_body(page: QWidget, margins: tuple[int, int, int, int] = (36, 28, 36, 28),
                 spacing: int = 18) -> QVBoxLayout:
    """Sayfayı dikeyde kaydırılabilir yapar (pencere küçülünce/bir kutu büyüyünce
    içerik birbirinin üstüne binmez, kaydırma çubuğu çıkar — web sayfası gibi).

    `page`'e tek bir QScrollArea koyar; asıl içerik onun içindeki bir QWidget'a
    eklenir. Dönen QVBoxLayout'a normal şekilde widget/layout eklemeye devam et."""
    outer = QVBoxLayout(page)
    outer.setContentsMargins(0, 0, 0, 0)
    outer.setSpacing(0)
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.NoFrame)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    scroll.setStyleSheet("QScrollArea { background: transparent; }")
    content = QWidget()
    content.setStyleSheet("background: transparent;")
    root = QVBoxLayout(content)
    root.setContentsMargins(*margins)
    root.setSpacing(spacing)
    root.setAlignment(Qt.AlignTop)
    scroll.setWidget(content)
    outer.addWidget(scroll)
    return root


def page_header(title: str, subtitle: str = "") -> tuple[QVBoxLayout, QLabel, QLabel]:
    lay = QVBoxLayout()
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)
    t = label(title, "H2", wrap=True)
    s = label(subtitle, "Subtle", wrap=True)
    lay.addWidget(t)
    lay.addWidget(s)
    if not subtitle:
        s.hide()
    return lay, t, s
