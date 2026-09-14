"""Ana ekran (Kapsam v2): solda kitap kuyruğu, sağda seçili kitabın özet paneli."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QListWidgetItem, QPushButton, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QVBoxLayout, QWidget,
)

from app.core.history import JobRecord
from app.core.history import format_duration
from app.core.i18n import tr
from app.core.paths import format_bytes
from app.core.queue import BookItem
from app.ui import theme
from app.ui.widgets import Card, label, svg_icon

ROW_H = 58
STATUS_COLORS = {
    "bekliyor": (theme.WARN, theme.WARN_SOFT),
    "test-suruyor": (theme.ACCENT_DARK, theme.ACCENT_SOFT),
    "test-tamam": (theme.SUCCESS, theme.SUCCESS_SOFT),
    "suruyor": (theme.ACCENT_DARK, theme.ACCENT_SOFT),
    "bitti": (theme.SUCCESS, theme.SUCCESS_SOFT),
    "hata": (theme.DANGER, "#fdecec"),
    "atlandi": (theme.TEXT_MUTED, theme.BG),
}


class _QueueDelegate(QStyledItemDelegate):
    """Bir satır: tutamak, sıra numarası, ad + alt bilgi, durum etiketi."""

    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), ROW_H)

    def paint(self, p: QPainter, option: QStyleOptionViewItem, index) -> None:
        book: BookItem = index.data(Qt.UserRole)
        r = option.rect
        selected = bool(option.state & QStyle.State_Selected)
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(r, QColor(theme.ACCENT_SOFT if selected else theme.SURFACE))
        if selected:
            p.fillRect(QRect(r.left(), r.top(), 3, r.height()), QColor(theme.ACCENT))
        p.setPen(QPen(QColor("#eef0f2")))
        p.drawLine(r.left(), r.bottom(), r.right(), r.bottom())
        # tutamak
        svg_icon("grip", "#b9c0c8", 16).paint(p, QRect(r.left() + 12, r.center().y() - 8, 16, 16))
        # numara
        n = index.row() + 1
        cx = r.left() + 40
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(theme.ACCENT if selected else theme.BORDER))
        p.drawEllipse(QRect(cx, r.center().y() - 11, 22, 22))
        f = QFont(option.font); f.setPointSizeF(8.5); f.setBold(True); p.setFont(f)
        p.setPen(QColor("#ffffff" if selected else theme.TEXT_SOFT))
        p.drawText(QRect(cx, r.center().y() - 11, 22, 22), Qt.AlignCenter, str(n))
        # durum etiketi (sağ)
        fg, bg = STATUS_COLORS.get(book.status, (theme.TEXT_MUTED, theme.BG))
        f2 = QFont(option.font); f2.setPointSizeF(8.5); f2.setBold(True)
        fm2 = QFontMetrics(f2)
        txt = book.status_label
        pw = fm2.horizontalAdvance(txt) + 18
        pill = QRect(r.right() - pw - 14, r.center().y() - 11, pw, 22)
        p.setPen(Qt.NoPen); p.setBrush(QColor(bg)); p.drawRoundedRect(pill, 11, 11)
        p.setFont(f2); p.setPen(QColor(fg)); p.drawText(pill, Qt.AlignCenter, txt)
        # ad ve alt bilgi
        left = cx + 34; width = pill.left() - left - 12
        f3 = QFont(option.font); f3.setPointSizeF(10); f3.setBold(True); p.setFont(f3); p.setPen(QColor(theme.TEXT))
        title = QFontMetrics(f3).elidedText(book.title, Qt.ElideRight, width)
        p.drawText(QRect(left, r.top() + 10, width, 20), Qt.AlignLeft | Qt.AlignVCenter, title)
        f4 = QFont(option.font); f4.setPointSizeF(8.5); p.setFont(f4); p.setPen(QColor(theme.TEXT_MUTED))
        sub = book.pdf_name
        if book.page_count:
            sub += " · " + tr("{n} sayfa", n=f"{book.page_count:,}".replace(",", "."))
        if book.size_bytes:
            sub += f" · {format_bytes(book.size_bytes)}"
        p.drawText(QRect(left, r.top() + 31, width, 18), Qt.AlignLeft | Qt.AlignVCenter,
                   QFontMetrics(f4).elidedText(sub, Qt.ElideMiddle, width))
        p.restore()


class QueueList(QListWidget):
    files_dropped = Signal(list)
    reordered = Signal(list)   # id listesi

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(_QueueDelegate(self))
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAcceptDrops(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setFrameShape(QFrame.NoFrame)
        self.setStyleSheet("QListWidget { background: transparent; border: none; }")
        self.model().rowsMoved.connect(lambda *_: self.reordered.emit(self.ids()))

    def ids(self) -> list[str]:
        return [self.item(i).data(Qt.UserRole).id for i in range(self.count())]

    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction(); return
        super().dragEnterEvent(e)

    def dragMoveEvent(self, e) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction(); return
        super().dragMoveEvent(e)

    def dropEvent(self, e: QDropEvent) -> None:
        if e.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in e.mimeData().urls() if u.toLocalFile().lower().endswith(".pdf")]
            if paths:
                self.files_dropped.emit(paths)
            e.acceptProposedAction(); return
        super().dropEvent(e)


def describe_book(b: BookItem) -> tuple[str, str, str]:
    """(başlık satırı, açıklama, öneri) — sağ paneldeki özet metinleri."""
    a = b.analysis or {}
    t = b.test
    if t and t.get("md_var"):
        head = tr("Test koşusu: ilk {n} sayfa çevrildi", n=t.get('sayfa', 50))
        if t.get("sure_sn"):
            head += f" ({format_duration(t['sure_sn'])})"
        parts = []
        parts.append(tr("Metin katmanı temiz.") if not a.get("is_scanned") and not a.get("text_is_broken")
                      else (tr("Kitap taranmış görünüyor.") if a.get("is_scanned") else tr("Metin katmanı var ama bozuk.")))
        parts.append(tr("{p} sayfada {denklem} denklem, {tablo} tablo satırı, {resim} şekil;",
                        p=t['sayfa'], denklem=t.get('denklem', 0), tablo=t.get('tablo', 0), resim=t.get('resim', 0)))
        parts.append((tr("boş denklem yok") if not t.get("bos_denklem") else tr("{n} boş denklem", n=t['bos_denklem'])) + ", " +
                     (tr("bozuk karakter yok.") if not t.get("bozuk_karakter") else tr("{n} bozuk karakter.", n=t['bozuk_karakter'])))
        if a.get("has_outline"):
            parts.append(tr("İçindekiler ağacı var: {n} başlık.", n=a.get('outline_count', 0)))
        else:
            parts.append(tr("İçindekiler ağacı yok, 40 sayfalık parçalara bölünecek."))
        desc = " ".join(parts)
        force = b.effective_force_ocr
        if not force:
            why = tr("metin katmanı temiz, hızlı mod yeterli")
        elif t.get("bos_denklem") or t.get("bozuk_karakter"):
            why = tr("test çıktısında bozuk denklem veya karakter görüldü, her sayfa görüntü olarak okunacak")
        elif a.get("is_scanned") or t.get("karakter_sayfa", 999) < 200:
            why = tr("sayfalarda çok az okunabilir metin var, kitap taranmış görünüyor")
        else:
            why = tr("metin katmanı güvenilir değil, her sayfa görüntü olarak okunacak")
        if b.force_ocr is not None:
            why = tr("kullanıcı elle seçti")
        rec = tr("{choice}: Zorunlu OCR {state}; {why}.",
                 choice=(tr("Seçim") if b.force_ocr is not None else tr("Öneri")),
                 state=(tr("açık") if force else tr("kapalı")), why=why)
        if t.get("sure_sn") and b.page_count:
            est = t["sure_sn"] / max(1, t["sayfa"]) * b.page_count
            rec += " " + tr("Tahmini süre yaklaşık {sure}.", sure=format_duration(est))
        return head, desc, rec
    if a:
        head = tr("Hızlı inceleme (test koşusu henüz yapılmadı)")
        desc = tr("Metin katmanı: {tl}. Tür: {kind}. İçindekiler: {outline}.",
                  tl=a.get('text_layer_label', '—'), kind=a.get('kind_label', '—'), outline=a.get('outline_label', '—'))
        rec = tr("Öneri: {reason}", reason=a.get('reason', ''))
        return head, desc, rec
    return tr("İnceleniyor…"), tr("PDF okunuyor, birkaç saniye sürer."), ""


class HomePage(QWidget):
    files_added = Signal(list)
    book_selected = Signal(str)
    rename_requested = Signal(str)
    change_file_requested = Signal(str)
    remove_requested = Signal(str)
    reordered = Signal(list)
    test_requested = Signal(str)
    start_all_requested = Signal()
    force_ocr_changed = Signal(str, object)     # id, True/False/None
    output_root_changed = Signal(str, str)
    open_output_requested = Signal(str)          # id
    recent_open_requested = Signal(str)          # job id
    show_history = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._selected: BookItem | None = None
        root = QHBoxLayout(self); root.setContentsMargins(28, 24, 28, 24); root.setSpacing(20)

        # ---- SOL ----
        left = QVBoxLayout(); left.setSpacing(14)
        head = QVBoxLayout(); head.setSpacing(4)
        head.addWidget(label(tr("Kitaplar"), "H2"))
        head.addWidget(label(tr("Sıraya PDF ekle, sürükleyerek sırala, tıklayıp sağda incele."), "Subtle", wrap=True))
        left.addLayout(head)

        self.queue_card = Card(padding=0, spacing=0)
        self.list = QueueList()
        self.list.itemSelectionChanged.connect(self._on_select)
        self.list.files_dropped.connect(self.files_added)
        self.list.reordered.connect(self.reordered)
        self.queue_card.body.addWidget(self.list, 1)
        self.empty = label(tr("Henüz kitap eklenmedi. PDF'leri sürükle ya da Dosya Ekle'ye bas."), "Subtle", wrap=True)
        self.empty.setAlignment(Qt.AlignCenter); self.empty.setContentsMargins(16, 28, 16, 28)
        self.queue_card.body.addWidget(self.empty)
        add_row = QWidget(); add_row.setStyleSheet(f"border-top: 1px dashed {theme.BORDER_STRONG};")
        al = QHBoxLayout(add_row); al.setContentsMargins(14, 10, 14, 10); al.setSpacing(10)
        self.add_button = QPushButton("  " + tr("Dosya Ekle")); self.add_button.setObjectName("Link")
        self.add_button.setIcon(svg_icon("plus", theme.ACCENT, 16, 2.2)); self.add_button.setCursor(Qt.PointingHandCursor)
        self.add_button.setStyleSheet(f"font-weight: 600; color: {theme.ACCENT}; border: none;")
        self.add_button.clicked.connect(self._pick_files)
        al.addStretch(); al.addWidget(self.add_button)
        al.addWidget(label(tr("veya PDF'leri buraya sürükle"), "Subtle")); al.addStretch()
        self.queue_card.body.addWidget(add_row)
        left.addWidget(self.queue_card, 1)

        acts = QHBoxLayout(); acts.setSpacing(8)
        acts.addWidget(label(tr("Seçili kitap için:"), "Subtle"))
        self.btn_rename = QPushButton(tr("Adını değiştir")); self.btn_change = QPushButton(tr("Dosyayı değiştir")); self.btn_remove = QPushButton(tr("Sıradan kaldır"))
        for b in (self.btn_rename, self.btn_change, self.btn_remove):
            b.setObjectName("Link"); b.setCursor(Qt.PointingHandCursor); b.setEnabled(False)
        self.btn_remove.setStyleSheet(f"color: {theme.DANGER};")
        self.btn_rename.clicked.connect(lambda: self._selected and self.rename_requested.emit(self._selected.id))
        self.btn_change.clicked.connect(lambda: self._selected and self.change_file_requested.emit(self._selected.id))
        self.btn_remove.clicked.connect(lambda: self._selected and self.remove_requested.emit(self._selected.id))
        acts.addWidget(self.btn_rename); acts.addWidget(label("·", "Subtle")); acts.addWidget(self.btn_change)
        acts.addWidget(label("·", "Subtle")); acts.addWidget(self.btn_remove); acts.addStretch()
        left.addLayout(acts)

        rh = QHBoxLayout(); rh.addWidget(label(tr("Son dönüştürülenler"), "SectionTitle")); rh.addStretch()
        see = QPushButton(tr("Tümünü gör")); see.setObjectName("Link"); see.setCursor(Qt.PointingHandCursor); see.clicked.connect(self.show_history)
        rh.addWidget(see); left.addLayout(rh)
        self.recent = QListWidget(); self.recent.setSelectionMode(QListWidget.NoSelection); self.recent.setFocusPolicy(Qt.NoFocus)
        self.recent.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff); self.recent.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        left.addWidget(self.recent)
        self.recent_empty = label(tr("Henüz dönüştürülmüş kitap yok."), "Subtle"); left.addWidget(self.recent_empty)

        leftw = QWidget(); leftw.setLayout(left); leftw.setFixedWidth(470)
        root.addWidget(leftw)

        # ---- SAĞ: özet paneli ----
        self.panel = Card(padding=20, spacing=12)
        self.sel_caption = label(tr("SEÇİLİ KİTAP"), "TileLabel"); self.sel_caption.setStyleSheet("letter-spacing: 1px; font-size: 8.5pt;")
        self.sel_title = label(tr("Bir kitap seç"), "SectionTitle"); self.sel_title.setStyleSheet("font-size: 12pt;"); self.sel_title.setWordWrap(True)
        cap = QVBoxLayout(); cap.setSpacing(2); cap.addWidget(self.sel_caption); cap.addWidget(self.sel_title)
        self.panel.body.addLayout(cap)

        self.summary = QFrame(); self.summary.setObjectName("StatTile")
        sl = QVBoxLayout(self.summary); sl.setContentsMargins(14, 12, 14, 12); sl.setSpacing(6)
        self.sum_head = label("", "SectionTitle"); self.sum_head.setWordWrap(True)
        self.sum_desc = label("", "Soft", wrap=True)
        self.sum_rec = label("", wrap=True); self.sum_rec.setStyleSheet(f"color: {theme.ACCENT_DARK}; font-weight: 600;")
        sl.addWidget(self.sum_head); sl.addWidget(self.sum_desc); sl.addWidget(self.sum_rec)
        self.panel.body.addWidget(self.summary)

        ocr = QHBoxLayout(); self.ocr_label = label(tr("Zorunlu OCR (force_ocr)")); ocr.addWidget(self.ocr_label); ocr.addStretch()
        self.ocr_note = label("", "Subtle"); ocr.addWidget(self.ocr_note)
        self.force_ocr = QCheckBox(""); self.force_ocr.setTristate(False)
        self.force_ocr.toggled.connect(self._on_force_toggle)
        ocr.addWidget(self.force_ocr)
        self.panel.body.addLayout(ocr)
        self.ocr_reset = QPushButton(tr("Öneriye dön")); self.ocr_reset.setObjectName("Link"); self.ocr_reset.setCursor(Qt.PointingHandCursor)
        self.ocr_reset.clicked.connect(lambda: self._selected and self.force_ocr_changed.emit(self._selected.id, None))
        self.panel.body.addWidget(self.ocr_reset, 0, Qt.AlignRight); self.ocr_reset.hide()

        out_l = QVBoxLayout(); out_l.setSpacing(6)
        self.out_caption = label(tr("Çıktı klasörü"), "Soft"); out_l.addWidget(self.out_caption)
        orow = QHBoxLayout(); orow.setSpacing(8)
        self.out_edit = QLineEdit(); self.out_edit.setReadOnly(True); orow.addWidget(self.out_edit, 1)
        self.browse = QPushButton(tr("Gözat…")); self.browse.setObjectName("Small"); self.browse.clicked.connect(self._browse); orow.addWidget(self.browse)
        self.open_folder = QPushButton("  " + tr("Klasöre Git")); self.open_folder.setObjectName("Small")
        self.open_folder.setIcon(svg_icon("folder", theme.TEXT, 14)); self.open_folder.clicked.connect(self._open_folder)
        orow.addWidget(self.open_folder)
        out_l.addLayout(orow)
        self.out_hint = label("", "TileLabel", wrap=True); out_l.addWidget(self.out_hint)
        self.panel.body.addLayout(out_l)

        self.preflight = QFrame(); self.preflight.setObjectName("InfoBanner")
        pl = QHBoxLayout(self.preflight); pl.setContentsMargins(10, 8, 10, 8)
        self.preflight_text = label("", "InfoText", wrap=True); self.preflight_text.setStyleSheet("font-size: 9pt;")
        pl.addWidget(self.preflight_text)
        self.panel.body.addWidget(self.preflight)

        self.panel.body.addStretch()
        self.btn_test = QPushButton(tr("Test koşusu ({n} sayfa)", n=50)); self.btn_test.setObjectName("Outline")
        self.btn_test.clicked.connect(lambda: self._selected and self.test_requested.emit(self._selected.id))
        self.btn_start = QPushButton("  " + tr("Dönüştür")); self.btn_start.setObjectName("Primary"); self.btn_start.setIcon(svg_icon("play", "#ffffff", 16))
        self.btn_start.clicked.connect(self.start_all_requested)
        self.start_hint = label(tr("Test yapılmamış kitaplar önce {n} sayfa test edilir, sonra tam koşuya geçer.", n=50), "TileLabel", wrap=True)
        self.start_hint.setAlignment(Qt.AlignCenter)
        self.panel.body.addWidget(self.btn_test); self.panel.body.addWidget(self.btn_start); self.panel.body.addWidget(self.start_hint)
        root.addWidget(self.panel, 1)
        self._show_selection(None)

    # ---------- veri ----------
    def set_books(self, books: list[BookItem], keep_selection: bool = True) -> None:
        cur = self._selected.id if (self._selected and keep_selection) else None
        self.list.blockSignals(True)
        self.list.clear()
        for b in books:
            it = QListWidgetItem(); it.setData(Qt.UserRole, b); it.setSizeHint(QSize(0, ROW_H))
            self.list.addItem(it)
            if b.id == cur:
                it.setSelected(True)
        self.list.blockSignals(False)
        self.empty.setVisible(not books); self.list.setVisible(bool(books))
        self.list.setFixedHeight(min(len(books), 5) * ROW_H + 2 if books else 0)
        n = len([b for b in books if b.status not in ("bitti", "atlandi")])
        self.btn_start.setText(("  " + tr("{n} kitabı sırayla dönüştür", n=n)) if n > 1 else ("  " + tr("Dönüştür")))
        self.btn_start.setEnabled(n > 0)
        sel = next((b for b in books if b.id == cur), None)
        self._show_selection(sel if sel else (books[0] if books and not cur else None))
        if sel is None and books and not cur:
            self.list.blockSignals(True); self.list.item(0).setSelected(True); self.list.blockSignals(False)

    def refresh_book(self, b: BookItem) -> None:
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole).id == b.id:
                self.list.item(i).setData(Qt.UserRole, b)
        if self._selected and self._selected.id == b.id:
            self._show_selection(b)
        self.list.viewport().update()

    def set_test_pages(self, n: int) -> None:
        self.btn_test.setText(tr("Test koşusu ({n} sayfa)", n=n))
        self.start_hint.setText(tr("Test yapılmamış kitaplar önce {n} sayfa test edilir, sonra tam koşuya geçer.", n=n))

    def set_preflight(self, text: str, warn: bool) -> None:
        self.preflight_text.setText(text)
        self.preflight_text.setStyleSheet(f"font-size: 9pt; color: {theme.WARN if warn else theme.ACCENT_DARK};")
        self.preflight.setVisible(bool(text))

    def set_recent(self, jobs: list[JobRecord]) -> None:
        self.recent.clear()
        jobs = jobs[:3]
        self.recent.setVisible(bool(jobs)); self.recent_empty.setVisible(not jobs)
        for j in jobs:
            row = QWidget(); h = QHBoxLayout(row); h.setContentsMargins(4, 0, 4, 0); h.setSpacing(12)
            h.addWidget(label(j.title or j.pdf_name), 1)
            h.addWidget(label(j.date_label, "Subtle"))
            exists = Path(j.output_dir).exists()
            btn = QPushButton(tr("Klasörü aç") if exists else tr("Klasör taşınmış")); btn.setObjectName("Link"); btn.setCursor(Qt.PointingHandCursor)
            if not exists:
                btn.setStyleSheet(f"color: {theme.DANGER};")
            btn.clicked.connect(lambda _=False, jid=j.id: self.recent_open_requested.emit(jid))
            h.addWidget(btn)
            it = QListWidgetItem(); it.setSizeHint(QSize(0, 38)); self.recent.addItem(it); self.recent.setItemWidget(it, row)
        self.recent.setFixedHeight(len(jobs) * 38 + 4 if jobs else 0)

    # ---------- iç ----------
    def _on_select(self) -> None:
        items = self.list.selectedItems()
        b = items[0].data(Qt.UserRole) if items else None
        self._show_selection(b)
        if b:
            self.book_selected.emit(b.id)

    def _show_selection(self, b: BookItem | None) -> None:
        self._selected = b
        has = b is not None
        for w in (self.btn_rename, self.btn_change, self.btn_remove, self.btn_test):
            w.setEnabled(has and (b.status not in ("suruyor", "test-suruyor") if has else False))
        for w in (self.summary, self.force_ocr, self.ocr_note, self.ocr_label, self.out_edit, self.out_hint,
                  self.out_caption, self.browse, self.open_folder, self.btn_test):
            w.setVisible(has)
        if not has:
            self.sel_title.setText(tr("Bir kitap seç")); self.sum_head.setText(""); self.preflight.hide(); self.ocr_reset.hide()
            return
        self.sel_title.setText(b.title)
        head, desc, rec = describe_book(b)
        self.sum_head.setText(head); self.sum_desc.setText(desc); self.sum_rec.setText(rec); self.sum_rec.setVisible(bool(rec))
        self.force_ocr.blockSignals(True); self.force_ocr.setChecked(b.effective_force_ocr); self.force_ocr.blockSignals(False)
        auto = b.force_ocr is None
        self.ocr_note.setText((tr("Açık") if b.effective_force_ocr else tr("Kapalı")) + (" · " + tr("öneri") if auto else " · " + tr("elle")))
        self.ocr_reset.setVisible(not auto)
        self.out_edit.setText(str(b.output_dir))
        has_output = b.status != "bekliyor"
        self.browse.setVisible(not has_output)
        self.open_folder.setVisible(has_output)
        self.out_hint.setText(
            tr("Kitap dosyaları bu klasörde.") if has_output else
            tr("Kitap klasörü adın altında oluşur. Kök klasör son kullanılan yerdir; Gözat ile değiştir.")
        )

    def _on_force_toggle(self, checked: bool) -> None:
        if self._selected:
            self.force_ocr_changed.emit(self._selected.id, bool(checked))

    def _browse(self) -> None:
        if not self._selected:
            return
        d = QFileDialog.getExistingDirectory(self, tr("Çıktı kök klasörünü seç"), self._selected.output_root or str(Path.home()))
        if d:
            self.output_root_changed.emit(self._selected.id, d)

    def _open_folder(self) -> None:
        if self._selected:
            self.open_output_requested.emit(self._selected.id)

    def _pick_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, tr("PDF kitapları seç"), str(Path.home()), tr("PDF dosyaları (*.pdf)"))
        if paths:
            self.files_added.emit(paths)
