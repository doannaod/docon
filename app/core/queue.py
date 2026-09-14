"""Kitap kuyruğu (Kapsam v2): sıralı, yeniden adlandırılabilir, diske kaydedilir (kuyruk.json)."""

from __future__ import annotations

import json
import re
import unicodedata
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.core.i18n import tr
from app.core.paths import app_data_dir

STATUS_LABELS = {
    "bekliyor": "Test bekliyor",
    "test-suruyor": "Test sürüyor",
    "test-tamam": "Test tamam",
    "suruyor": "Dönüştürülüyor",
    "bitti": "Bitti",
    "hata": "Hata",
    "atlandi": "Atlandı",
}


def slug(text: str, uz: int = 60) -> str:
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return re.sub(r"-{2,}", "-", t)[:uz] or "kitap"


def guess_title(pdf_path: str) -> str:
    """'2019_Book_FundamentalsOfHeat_FINAL.pdf' -> 'Fundamentals Of Heat FINAL'"""
    s = Path(pdf_path).stem
    s = re.sub(r"^\d{4}_Book_", "", s)
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    s = s.replace("_", " ").replace("-", " ")
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s[:80] or Path(pdf_path).stem


@dataclass
class BookItem:
    pdf_path: str
    title: str
    output_root: str                       # kitap klasörü bunun altında: <root>/<slug(title)>
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    force_ocr: bool | None = None          # None = otomatik (öneri)
    status: str = "bekliyor"
    page_count: int = 0
    size_bytes: int = 0
    analysis: dict | None = None           # analyzer özeti (hızlı)
    test: dict | None = None               # kosucu test_sonuc
    job_id: str | None = None              # HistoryStore kaydı
    message: str = ""

    @property
    def pdf_name(self) -> str:
        return Path(self.pdf_path).name

    @property
    def output_dir(self) -> Path:
        return Path(self.output_root) / slug(self.title)

    @property
    def status_label(self) -> str:
        return tr(STATUS_LABELS.get(self.status, self.status))

    @property
    def effective_force_ocr(self) -> bool:
        if self.force_ocr is not None:
            return self.force_ocr
        if self.test and self.test.get("oneri_force_ocr") is not None:
            return bool(self.test["oneri_force_ocr"])
        if self.analysis:
            return bool(self.analysis.get("recommend_force_ocr"))
        return False


class BookQueue:
    def __init__(self, path: Path | None = None):
        self.path = path or (app_data_dir() / "kuyruk.json")
        self.items: list[BookItem] = []
        self.load()

    def load(self) -> None:
        self.items = []
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        known = set(BookItem.__dataclass_fields__)
        for it in data.get("items", []):
            self.items.append(BookItem(**{k: v for k, v in it.items() if k in known}))
        # program kapanırken sürüyor kalanlar tekrar bekler
        for b in self.items:
            if b.status in ("suruyor", "test-suruyor"):
                b.status = "test-tamam" if b.test else "bekliyor"

    def save(self) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": 1, "items": [asdict(b) for b in self.items]},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def add(self, pdf_path: str, output_root: str) -> BookItem | None:
        if any(b.pdf_path.lower() == pdf_path.lower() for b in self.items):
            return None
        p = Path(pdf_path)
        b = BookItem(pdf_path=pdf_path, title=guess_title(pdf_path), output_root=output_root,
                     size_bytes=p.stat().st_size if p.exists() else 0)
        self.items.append(b)
        self.save()
        return b

    def get(self, book_id: str) -> BookItem | None:
        return next((b for b in self.items if b.id == book_id), None)

    def remove(self, book_id: str) -> None:
        self.items = [b for b in self.items if b.id != book_id]
        self.save()

    def reorder(self, ids: list[str]) -> None:
        by = {b.id: b for b in self.items}
        self.items = [by[i] for i in ids if i in by] + [b for b in self.items if b.id not in ids]
        self.save()

    def pending(self) -> list[BookItem]:
        return [b for b in self.items if b.status not in ("bitti", "atlandi")]

    def clear_finished(self) -> None:
        self.items = [b for b in self.items if b.status not in ("bitti", "atlandi")]
        self.save()
