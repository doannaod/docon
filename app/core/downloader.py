"""Kesintiye dayanıklı HTTP indirici (talimat 5.1): Range ile kaldığı yerden devam, yeniden deneme,
anlık hız ve tahmini kalan süre. Yalnızca standart kütüphane kullanır.
"""

from __future__ import annotations

import threading
import time
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from app.core.i18n import tr

CHUNK = 1024 * 256
USER_AGENT = "DonusumProgrami/0.1 (+Windows)"


class DownloadCancelled(Exception):
    pass


class DownloadError(Exception):
    pass


@dataclass
class Progress:
    done: int
    total: int          # 0 = bilinmiyor
    speed_bps: float    # son ~5 sn ortalaması
    eta_sec: float | None


class SpeedMeter:
    def __init__(self, window_sec: float = 5.0):
        self.window = window_sec
        self.samples: deque[tuple[float, int]] = deque()

    def add(self, done_bytes: int) -> float:
        now = time.monotonic()
        self.samples.append((now, done_bytes))
        while self.samples and now - self.samples[0][0] > self.window:
            self.samples.popleft()
        if len(self.samples) < 2:
            return 0.0
        (t0, b0), (t1, b1) = self.samples[0], self.samples[-1]
        return (b1 - b0) / (t1 - t0) if t1 > t0 else 0.0


def head_size(url: str, timeout: float = 20) -> int:
    """Content-Length; bilinmiyorsa 0."""
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return int(r.headers.get("Content-Length") or 0)
    except Exception:
        try:  # bazı sunucular HEAD'i sevmez
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                cr = r.headers.get("Content-Range", "")
                if "/" in cr:
                    return int(cr.rsplit("/", 1)[1])
                return int(r.headers.get("Content-Length") or 0)
        except Exception:
            return 0


def download(url: str, dest: Path, on_progress: Callable[[Progress], None] | None = None,
             cancel: threading.Event | None = None, retries: int = 8, timeout: float = 30,
             expected_size: int = 0, base_done: int = 0, base_total: int = 0) -> Path:
    """`dest.part` dosyasına indirir, bitince `dest` adına taşır. Var olan .part'tan devam eder.

    base_done / base_total: birden çok dosyalık toplu indirmede toplam ilerlemeyi raporlamak için
    önceki dosyaların baytları eklenir.
    """
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and (not expected_size or dest.stat().st_size == expected_size):
        if on_progress:
            size = dest.stat().st_size
            on_progress(Progress(base_done + size, base_total or size, 0.0, 0.0))
        return dest

    part = dest.with_suffix(dest.suffix + ".part")
    total = expected_size or head_size(url)
    meter = SpeedMeter()
    attempt = 0
    while True:
        if cancel and cancel.is_set():
            raise DownloadCancelled()
        have = part.stat().st_size if part.exists() else 0
        if total and have >= total:
            break
        headers = {"User-Agent": USER_AGENT}
        if have:
            headers["Range"] = f"bytes={have}-"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if have and r.status != 206:
                    # sunucu devam desteklemiyor: baştan
                    have = 0
                    part.unlink(missing_ok=True)
                if not total:
                    cl = int(r.headers.get("Content-Length") or 0)
                    total = have + cl if cl else 0
                with open(part, "ab" if have else "wb") as f:
                    while True:
                        if cancel and cancel.is_set():
                            raise DownloadCancelled()
                        chunk = r.read(CHUNK)
                        if not chunk:
                            break
                        f.write(chunk)
                        have += len(chunk)
                        if on_progress:
                            spd = meter.add(base_done + have)
                            remaining = (base_total or total) - (base_done + have) if (base_total or total) else 0
                            eta = remaining / spd if spd > 0 and remaining > 0 else None
                            on_progress(Progress(base_done + have, base_total or total, spd, eta))
            if total and have < total:
                raise DownloadError(tr("bağlantı erken kapandı"))
            break
        except DownloadCancelled:
            raise
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ConnectionError, OSError, DownloadError) as e:
            attempt += 1
            if attempt > retries:
                raise DownloadError(f"{url} indirilemedi ({attempt - 1} deneme): {e}") from e
            wait = min(60, 2 ** attempt)
            if on_progress:
                on_progress(Progress(base_done + have, base_total or total, 0.0, None))
            # yeniden denemeden önce bekle (iptal edilebilir)
            for _ in range(int(wait * 10)):
                if cancel and cancel.is_set():
                    raise DownloadCancelled()
                time.sleep(0.1)
    part.replace(dest)
    return dest
