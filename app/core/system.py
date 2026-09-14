"""Sistem yardımcıları: tek örnek kilidi, uyku engelleme, disk ve GPU denetimi, GPU izleme, ham klasör temizliği."""

from __future__ import annotations

import ctypes
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QTimer, Signal

from app.core.i18n import tr
from app.core.paths import app_data_dir, folder_size_bytes

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


# ---------- tek örnek ----------
class SingleInstance:
    def __init__(self):
        self._lock = QLockFile(str(app_data_dir() / "calisiyor.lock"))
        # NOT: setStaleLockTime(0) burada ÖNCEDEN kullanılıyordu ve tek-örnek korumasını
        # tamamen bozuyordu — Qt, 0 değerini "hiçbir zaman eskimiş sayma" değil, tam tersi
        # "her zaman eskimiş say" olarak yorumluyor; bu yüzden ikinci kopya da kilidi alıp
        # açılabiliyordu (paketleme testinde gerçek programla doğrulandı). Varsayılan süre
        # (30 sn) hem çökme sonrası kilidin makul sürede açılmasını hem de gerçekten çalışan
        # bir kopyanın anında tespit edilmesini sağlıyor.

    def acquire(self) -> bool:
        return self._lock.tryLock(100)


# ---------- uyku engelleme ----------
_ES_CONTINUOUS = 0x80000000
_ES_SYSTEM_REQUIRED = 0x00000001


def keep_awake(on: bool) -> None:
    if not sys.platform.startswith("win"):
        return
    try:
        flags = _ES_CONTINUOUS | (_ES_SYSTEM_REQUIRED if on else 0)
        ctypes.windll.kernel32.SetThreadExecutionState(flags)
    except Exception:
        pass


# ---------- GPU ----------
@dataclass
class GpuSample:
    name: str
    temp_c: int | None
    util_pct: int | None
    mem_used_mb: int | None
    mem_total_mb: int | None


def gpu_query() -> GpuSample | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,temperature.gpu,utilization.gpu,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5, creationflags=NO_WINDOW)
        if out.returncode != 0 or not out.stdout.strip():
            return None
        parts = [p.strip() for p in out.stdout.strip().splitlines()[0].split(",")]
        def num(s):
            try:
                return int(float(s))
            except ValueError:
                return None
        return GpuSample(parts[0], num(parts[1]), num(parts[2]), num(parts[3]), num(parts[4]))
    except (OSError, subprocess.TimeoutExpired, IndexError):
        return None


class GpuMonitor(QObject):
    """2 saniyede bir nvidia-smi; GPU yoksa hiç sinyal vermez."""
    sample = Signal(object)  # GpuSample

    def __init__(self, interval_ms: int = 2000, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self); self.timer.setInterval(interval_ms); self.timer.timeout.connect(self._tick)
        self.available = gpu_query() is not None

    def start(self) -> None:
        if self.available:
            self._tick(); self.timer.start()

    def stop(self) -> None:
        self.timer.stop()

    def _tick(self) -> None:
        s = gpu_query()
        if s:
            self.sample.emit(s)


# ---------- ön kontrol ----------
@dataclass
class PreflightResult:
    disk_free_gb: float
    disk_need_gb: float
    gpu: GpuSample | None
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not any(w.startswith("!") for w in self.warnings)


def preflight(output_dir: Path, pdf_bytes: int, install_needed: bool) -> PreflightResult:
    target = output_dir if output_dir.exists() else next((p for p in output_dir.parents if p.exists()), Path.home())
    free = shutil.disk_usage(target).free / 1024**3
    need = (pdf_bytes * 6) / 1024**3 + 0.5          # ham bloklar + görseller + md, kaba tahmin
    warnings: list[str] = []
    if install_needed:
        inst_free = shutil.disk_usage(app_data_dir()).free / 1024**3
        if inst_free < 12:
            warnings.append("! " + tr("Kurulum için C: sürücüsünde en az 12 GB boş alan gerekir, şu an {free} GB var.", free=f"{inst_free:.0f}"))
    if free < need:
        warnings.append("! " + tr("Çıktı sürücüsünde {need} GB gerekiyor, {free} GB boş var.", need=f"{need:.1f}", free=f"{free:.1f}"))
    gpu = gpu_query()
    if gpu is None:
        warnings.append(tr("NVIDIA ekran kartı bulunamadı; dönüştürme işlemciyle çok yavaş olur."))
    elif gpu.mem_total_mb and gpu.mem_total_mb < 8000:
        warnings.append(tr("Ekran kartı belleği {gb} GB; marker 8 GB altında yavaşlayabilir.", gb=f"{gpu.mem_total_mb / 1024:.0f}"))
    return PreflightResult(free, need, gpu, warnings)


# ---------- ham klasör temizliği ----------
def find_raw_dirs(output_dirs: list[Path]) -> list[Path]:
    found = []
    for d in output_dirs:
        raw = Path(d) / "_ham-ocr"
        if raw.exists():
            found.append(raw)
    return found


def clean_raw_dirs(dirs: list[Path]) -> int:
    freed = 0
    for d in dirs:
        freed += folder_size_bytes(d)
        shutil.rmtree(d, ignore_errors=True)
    return freed
