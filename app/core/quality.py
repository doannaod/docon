"""Kalite taraması: kitap bittikten sonra bölüm md dosyalarını tarar, sayılarla özetler."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from app.core.i18n import tr

BOS_ARRAY = re.compile(r"^\$\$\\begin\{array\}\{[a-z|]*\s*\$\$$")
BOS_DENK = re.compile(r"^\$\$\s*\$\$$")
RESIM_RE = re.compile(r"!\[\]\(([^)]+)\)")
TABLO_SATIR = re.compile(r"^\|.*\|\s*$")


@dataclass
class QualityReport:
    files: int = 0
    empty_equations: int = 0      # A: içerik kaybı
    missing_images: int = 0       # C
    unbalanced_latex: int = 0     # D
    weak_tables: int = 0          # E (%70+ boş hücre)
    table_spacing: int = 0        # G (tablo sonrası boş satır yok)
    details: list[str] = field(default_factory=list)

    @property
    def severe(self) -> int:
        return self.empty_equations + self.missing_images

    def summary(self) -> str:
        parts = []
        if self.empty_equations: parts.append(tr("{n} boş denklem", n=self.empty_equations))
        if self.missing_images: parts.append(tr("{n} eksik resim", n=self.missing_images))
        if self.unbalanced_latex: parts.append(tr("{n} dengesiz LaTeX", n=self.unbalanced_latex))
        if self.weak_tables: parts.append(tr("{n} zayıf tablo", n=self.weak_tables))
        if self.table_spacing: parts.append(tr("{n} tablo boşluğu", n=self.table_spacing))
        return ", ".join(parts) if parts else tr("Kusur bulunamadı")


def scan(folder: Path) -> QualityReport:
    r = QualityReport()
    folder = Path(folder)
    mds = [p for p in folder.glob("*.md") if p.name not in ("birlesik.md", "00-index.md", "00-kalite-raporu.md")]
    r.files = len(mds)
    for md in mds:
        try:
            lines = md.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        text = "\n".join(lines)
        for ln in lines:
            s = ln.strip()
            if BOS_ARRAY.match(s) or BOS_DENK.match(s):
                r.empty_equations += 1
        for m in RESIM_RE.finditer(text):
            if not (folder / m.group(1)).exists():
                r.missing_images += 1
        if text.count(r"\begin{array}") != text.count(r"\end{array}"):
            r.unbalanced_latex += 1
        # tablolar
        i = 0
        while i < len(lines):
            if TABLO_SATIR.match(lines[i]):
                j = i
                cells = 0; empty = 0
                while j < len(lines) and TABLO_SATIR.match(lines[j]):
                    row = [c.strip() for c in lines[j].strip().strip("|").split("|")]
                    if not all(set(c) <= set("-: ") for c in row):
                        cells += len(row); empty += sum(1 for c in row if not c)
                    j += 1
                if cells and empty / cells >= 0.7:
                    r.weak_tables += 1
                if j < len(lines) and lines[j].strip():
                    r.table_spacing += 1
                i = j
            else:
                i += 1
    lines_out = ["# Kalite raporu", "", f"Taranan dosya: {r.files}", "", f"Özet: {r.summary()}", "",
                 "| Kod | Kusur | Adet | Otomatik düzelir? |", "|---|---|---|---|",
                 f"| A | Boş denklem bloğu (içerik kaybı) | {r.empty_equations} | Hayır, elle |",
                 f"| C | Eksik resim dosyası | {r.missing_images} | Hayır |",
                 f"| D | Dengesiz LaTeX | {r.unbalanced_latex} | Hayır |",
                 f"| E | Zayıf tablo (%70+ boş hücre) | {r.weak_tables} | Hayır |",
                 f"| G | Tablo sonrası boş satır yok | {r.table_spacing} | Evet |"]
    try:
        (folder / "00-kalite-raporu.md").write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    except OSError:
        pass
    return r
