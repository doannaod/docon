"""Geçmiş işler kaydı (talimat 4.4, 4.6, 4.7). JSON dosyası: %LOCALAPPDATA%/Docon/gecmis.json"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

from app.core.i18n import tr
from app.core.paths import history_file

STATUS_LABELS = {
    "running": "Sürüyor",
    "paused": "Yarım kaldı",
    "done": "Tamamlandı",
    "error": "Hata",
}


@dataclass
class JobRecord:
    pdf_path: str
    output_dir: str
    force_ocr: bool
    page_count: int
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    status: str = "running"
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    finished_at: str | None = None
    total_blocks: int = 0
    done_blocks: int = 0
    chapters: int = 0
    appendices: int = 0
    figures: int = 0
    input_bytes: int = 0
    output_bytes: int = 0
    duration_sec: int = 0
    log_path: str | None = None
    message: str = ""
    title: str = ""                 # kullanıcının verdiği kitap adı (Kapsam v2)
    quality: str = ""               # kalite özeti

    # --- görünüm yardımcıları ---
    @property
    def pdf_name(self) -> str:
        return Path(self.pdf_path).name

    @property
    def display_name(self) -> str:
        return self.title or self.pdf_name

    @property
    def status_label(self) -> str:
        if self.status == "paused" and self.total_blocks:
            return tr("Yarım {done}/{total}", done=self.done_blocks, total=self.total_blocks)
        return tr(STATUS_LABELS.get(self.status, self.status))

    @property
    def started(self) -> datetime:
        return datetime.fromisoformat(self.started_at)

    @property
    def date_label(self) -> str:
        return format_date(self.started)

    @property
    def duration_label(self) -> str:
        return format_duration(self.duration_sec)


TR_MONTHS = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]


def format_date(dt: datetime) -> str:
    month = tr(TR_MONTHS[dt.month - 1])
    return f"{dt.day} {month} {dt.year}"


def format_duration(seconds: int | float) -> str:
    seconds = int(seconds)
    if seconds < 60:
        return tr("{n} sn", n=seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return tr("{h} sa {m} dk", h=h, m=f"{m:02d}")
    if m >= 10:
        return tr("{n} dk", n=m)
    return tr("{m} dk {s} sn", m=m, s=f"{s:02d}")


class HistoryStore:
    def __init__(self, path: Path | None = None):
        self.path = path or history_file()
        self._records: list[JobRecord] = []
        self.load()

    def load(self) -> None:
        self._records = []
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        known = set(JobRecord.__dataclass_fields__)
        for item in data.get("jobs", []):
            self._records.append(JobRecord(**{k: v for k, v in item.items() if k in known}))

    def save(self) -> None:
        payload = {"version": 1, "jobs": [asdict(r) for r in self._records]}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def add(self, record: JobRecord) -> JobRecord:
        self._records.append(record)
        self.save()
        return record

    def update(self, record: JobRecord) -> None:
        for i, r in enumerate(self._records):
            if r.id == record.id:
                self._records[i] = record
                break
        else:
            self._records.append(record)
        self.save()

    def get(self, job_id: str) -> JobRecord | None:
        return next((r for r in self._records if r.id == job_id), None)

    def all(self) -> list[JobRecord]:
        return sorted(self._records, key=lambda r: r.started_at, reverse=True)

    def unfinished(self) -> list[JobRecord]:
        return [r for r in self.all() if r.status in ("paused", "running")]

    def completed(self) -> list[JobRecord]:
        return [r for r in self.all() if r.status == "done"]
