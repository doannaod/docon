"""PDF ön analizi (talimat 3.6): metin katmanı var mı, taranmış mı, force_ocr gerekli mi?

Karar mantığı (talimat 2, "force_ocr kararı"):
- Örneklenen sayfaların çoğunda anlamlı metin varsa ve metin temizse  -> force_ocr KAPALI (hızlı).
- Sayfaların çoğu metinsizse (taranmış)                               -> force_ocr AÇIK.
- Metin var ama bozuk (çözümlenemeyen karakter, (cid:NN) kalıntısı,
  aşırı tek-harf/boşluk kırıntısı)                                     -> force_ocr AÇIK.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

from app.core.i18n import tr

# pypdf'in yazı tipi uyarıları kullanıcıyı ilgilendirmez
logging.getLogger("pypdf").setLevel(logging.ERROR)

MIN_CHARS_FOR_TEXT_PAGE = 80
SCANNED_TEXT_RATIO = 0.35        # bunun altı: taranmış say
BROKEN_CHAR_RATIO = 0.03         # bozuk karakter oranı bunun üstü: bozuk say
CID_PATTERN = re.compile(r"\(cid:\d+\)")
PRIVATE_USE = re.compile(r"[-�]")


@dataclass
class PdfAnalysis:
    path: Path
    size_bytes: int
    page_count: int
    sampled_pages: int
    text_pages: int
    text_ratio: float
    avg_chars_per_text_page: float
    broken_char_ratio: float
    encrypted: bool
    has_outline: bool
    outline_count: int
    outline_titles: list[str] = field(default_factory=list)
    error: str | None = None

    # --- karar ---
    @property
    def is_scanned(self) -> bool:
        return self.text_ratio < SCANNED_TEXT_RATIO

    @property
    def text_is_broken(self) -> bool:
        return (not self.is_scanned) and self.broken_char_ratio > BROKEN_CHAR_RATIO

    @property
    def recommend_force_ocr(self) -> bool:
        return self.is_scanned or self.text_is_broken

    @property
    def text_layer_label(self) -> str:
        if self.is_scanned:
            return tr("Yok veya çok az")
        if self.text_is_broken:
            return tr("Var, bozuk")
        return tr("Var, temiz")

    @property
    def kind_label(self) -> str:
        return tr("Taranmış (görüntü)") if self.is_scanned else tr("Dijital (taranmamış)")

    @property
    def outline_label(self) -> str:
        if not self.has_outline:
            return tr("Yok (40 sayfalık parça)")
        return tr("{n} başlık", n=self.outline_count)

    @property
    def reason(self) -> str:
        if self.is_scanned:
            return tr("Sayfaların çoğunda metin katmanı yok, kitap taranmış görünüyor. "
                      "Her sayfa görüntü olarak işlenecek; daha yavaş ama doğru.")
        if self.text_is_broken:
            return tr("Metin katmanı var ama bozuk karakterler içeriyor (denklem ve indisler "
                      "yanlış çıkabilir). Zorunlu OCR daha doğru sonuç verir.")
        return tr("Metin katmanı temiz, hızlı mod yeterli. Denklemler bozuk çıkarsa açabilirsin.")


def _sample_indices(page_count: int, sample: int) -> list[int]:
    if page_count <= sample:
        return list(range(page_count))
    step = page_count / sample
    return sorted({int(i * step) for i in range(sample)})


def _flatten_outline(outline, depth: int = 0, acc: list[str] | None = None) -> list[str]:
    acc = [] if acc is None else acc
    for item in outline:
        if isinstance(item, list):
            _flatten_outline(item, depth + 1, acc)
        else:
            title = getattr(item, "title", None)
            if title:
                acc.append(("  " * depth) + str(title).strip())
    return acc


def analyze_pdf(path: str | Path, sample: int = 40) -> PdfAnalysis:
    path = Path(path)
    size = path.stat().st_size
    try:
        reader = PdfReader(str(path))
        encrypted = bool(reader.is_encrypted)
        if encrypted:
            try:
                reader.decrypt("")
            except Exception:
                pass
        page_count = len(reader.pages)

        text_pages = 0
        total_chars = 0
        broken_chars = 0
        idx = _sample_indices(page_count, sample)
        for i in idx:
            try:
                text = reader.pages[i].extract_text() or ""
            except Exception:
                text = ""
            stripped = re.sub(r"\s+", "", text)
            if len(stripped) >= MIN_CHARS_FOR_TEXT_PAGE:
                text_pages += 1
                total_chars += len(stripped)
                broken_chars += len(PRIVATE_USE.findall(stripped))
                broken_chars += 6 * len(CID_PATTERN.findall(text))

        sampled = len(idx)
        text_ratio = text_pages / sampled if sampled else 0.0
        avg_chars = total_chars / text_pages if text_pages else 0.0
        broken_ratio = broken_chars / total_chars if total_chars else 0.0

        titles: list[str] = []
        try:
            titles = _flatten_outline(reader.outline)
        except Exception:
            titles = []

        return PdfAnalysis(
            path=path, size_bytes=size, page_count=page_count, sampled_pages=sampled,
            text_pages=text_pages, text_ratio=text_ratio, avg_chars_per_text_page=avg_chars,
            broken_char_ratio=broken_ratio, encrypted=encrypted,
            has_outline=bool(titles), outline_count=len(titles), outline_titles=titles[:60],
        )
    except Exception as exc:  # okunamayan PDF
        return PdfAnalysis(
            path=path, size_bytes=size, page_count=0, sampled_pages=0, text_pages=0,
            text_ratio=0.0, avg_chars_per_text_page=0.0, broken_char_ratio=0.0,
            encrypted=False, has_outline=False, outline_count=0, error=str(exc),
        )
