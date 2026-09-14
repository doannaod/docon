"""İlk kurulum (talimat 3.8, 4.0–4.2): programın kendi çalışma ortamını kurar.

Adımlar (her biri bittiğinde bir işaret dosyası yazılır; yeniden başlatınca biten adım atlanır):
  python    gömülü Python 3.12 + pip               -> runtime/.python-tamam
  packages  torch (cu126), marker-pdf, scipy, pypdf -> runtime/.paketler-tamam
            (pip'e "hangi dosyaları kuracaksın" diye sorulur, dosyalar kendi indiricimizle
             kesintiye dayanıklı indirilir, sonra çevrimdışı kurulur)
  models    surya modelleri (marker kendisi indirir; önbellek boyutu izlenir, kopmada tekrar
            denenir, tamamlanmış model dosyaları korunur) -> models/.docon-tamam
  verify    import + CUDA denetimi
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import threading
import time
import zipfile
from pathlib import Path
from urllib.parse import unquote

from PySide6.QtCore import QThread, Signal

from app.core.downloader import DownloadCancelled, DownloadError, Progress, SpeedMeter, download, head_size
from app.core.environment import MARKER_VERSION, SETUP_STEPS, TORCH_INDEX
from app.core.i18n import tr
from app.core.paths import app_data_dir, models_cache_dir, runtime_dir

PYTHON_VERSION = "3.12.10"
PYTHON_EMBED_URL = f"https://www.python.org/ftp/python/{PYTHON_VERSION}/python-{PYTHON_VERSION}-embed-amd64.zip"
GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"
SCIPY_VERSION = "1.15.3"

PACKAGE_GROUPS = [
    # (ad, gereksinimler, ek pip argümanları)
    # Tek planda çözülür: pip, cu126 dizinindeki "2.x+cu126" torch'u PyPI'dekine tercih eder
    # (PEP 440 yerel sürüm sıralaması); böylece torch ile marker arasında sürüm çakışması olmaz.
    # Doğrulandı 2026-09-13: torch 2.14.0+cu126, marker-pdf 1.10.2, scipy 1.15.3, 82 paket.
    ("paketler", ["torch", "torchvision", f"marker-pdf=={MARKER_VERSION}", f"scipy=={SCIPY_VERSION}", "pypdf"],
     ["--extra-index-url", TORCH_INDEX]),
]
MODEL_RETRIES = 6
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class InstallCancelled(Exception):
    pass


class InstallWorker(QThread):
    """Sinyaller arayüze: adım durumu, toplu ilerleme, mesaj, bitiş."""

    # Bayt sayıları 2 GB'ı aştığı için int yerine float taşınır (Qt int 32 bit)
    step_state = Signal(str, str, float, float)          # key, state, done_bytes, total_bytes
    progress = Signal(float, float, object, float, float)  # fraction, speed_bps, eta_sec|None, done, total
    message = Signal(str)
    finished_ok = Signal()
    failed = Signal(str)
    paused = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cancel = threading.Event()
        self.rt = runtime_dir()
        self.py = self.rt / "python.exe"
        self.dl_dir = app_data_dir() / "indirilenler"
        self.log_path = app_data_dir() / "loglar" / "kurulum.log"
        self._proc: subprocess.Popen | None = None
        # adım toplamları (bayt): gerçek boyut öğrenilince güncellenir
        self.totals = {k: b for k, _, b in SETUP_STEPS}
        self.dones = {k: 0 for k, _, _ in SETUP_STEPS}
        self._meter = SpeedMeter()

    # ---------- yardımcılar ----------
    def _log(self, text: str) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {text}\n")

    def _check_cancel(self) -> None:
        if self.cancel.is_set():
            raise InstallCancelled()

    def _emit_overall(self, speed: float | None = None, eta: float | None = None) -> None:
        done = sum(self.dones.values()); total = sum(self.totals.values())
        frac = done / total if total else 0.0
        if speed is None:
            speed = self._meter.add(done)
        if eta is None and speed and speed > 0:
            eta = (total - done) / speed
        self.progress.emit(frac, float(speed or 0.0), eta, float(done), float(total))

    def _on_dl(self, key: str):
        def cb(p: Progress):
            self.dones[key] = p.done
            if p.total:
                self.totals[key] = p.total
            self.step_state.emit(key, "running", p.done, self.totals[key])
            self._emit_overall(p.speed_bps, p.eta_sec)
        return cb

    def _run(self, args: list[str], timeout: float | None = None, env: dict | None = None) -> subprocess.CompletedProcess:
        """Alt süreç; çıktı log dosyasına. İptalde süreç öldürülür."""
        self._log("$ " + " ".join(str(a) for a in args))
        full_env = os.environ.copy()
        full_env["PYTHONIOENCODING"] = "utf-8"
        if env:
            full_env.update(env)
        with open(self.log_path, "a", encoding="utf-8", errors="replace") as f:
            self._proc = subprocess.Popen([str(a) for a in args], stdout=f, stderr=subprocess.STDOUT,
                                          creationflags=NO_WINDOW, env=full_env, cwd=str(self.rt))
            start = time.monotonic()
            while self._proc.poll() is None:
                if self.cancel.is_set():
                    self._kill()
                    raise InstallCancelled()
                if timeout and time.monotonic() - start > timeout:
                    self._kill()
                    raise RuntimeError(tr("işlem zaman aşımına uğradı"))
                time.sleep(0.2)
            rc = self._proc.returncode
            self._proc = None
        return subprocess.CompletedProcess(args, rc)

    def _kill(self) -> None:
        if self._proc and self._proc.poll() is None:
            subprocess.run(["taskkill", "/PID", str(self._proc.pid), "/T", "/F"], capture_output=True, creationflags=NO_WINDOW)

    # ---------- adımlar ----------
    def step_python(self) -> None:
        key = "python"
        flag = self.rt / ".python-tamam"
        if flag.exists() and self.py.exists():
            self.dones[key] = self.totals[key]; self.step_state.emit(key, "done", self.dones[key], self.totals[key]); return
        self.step_state.emit(key, "running", 0, self.totals[key])
        self.message.emit(tr("Python çalışma ortamı indiriliyor…"))
        zip_path = self.dl_dir / f"python-{PYTHON_VERSION}-embed-amd64.zip"
        getpip = self.dl_dir / "get-pip.py"
        sz = head_size(PYTHON_EMBED_URL); sz2 = head_size(GET_PIP_URL)
        self.totals[key] = (sz + sz2) or self.totals[key]
        download(PYTHON_EMBED_URL, zip_path, self._on_dl(key), self.cancel, expected_size=sz, base_total=self.totals[key])
        download(GET_PIP_URL, getpip, self._on_dl(key), self.cancel, expected_size=sz2, base_done=sz, base_total=self.totals[key])
        self._check_cancel()
        self.message.emit(tr("Python açılıyor ve pip kuruluyor…"))
        if self.rt.exists():
            shutil.rmtree(self.rt, ignore_errors=True)
        self.rt.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(self.rt)
        # gömülü Python'da site-packages'ı aç
        pth = next(self.rt.glob("python*._pth"))
        pth.write_text("python312.zip\n.\nLib\\site-packages\nimport site\n", encoding="utf-8")
        (self.rt / "Lib" / "site-packages").mkdir(parents=True, exist_ok=True)
        r = self._run([self.py, getpip, "--no-warn-script-location"], timeout=600)
        if r.returncode != 0:
            raise RuntimeError(tr("pip kurulamadı (kurulum.log)"))
        flag.write_text("ok", encoding="utf-8")
        self.dones[key] = self.totals[key]
        self.step_state.emit(key, "done", self.dones[key], self.totals[key])
        self._emit_overall()

    def _resolve(self, reqs: list[str], extra: list[str]) -> list[dict]:
        """pip'e kurulum planını sordur: [{name, version, url}]"""
        report = self.dl_dir / "pip-rapor.json"
        report.unlink(missing_ok=True)
        r = self._run([self.py, "-m", "pip", "install", "--dry-run", "--quiet", "--report", report,
                       "--no-warn-script-location", *reqs, *extra], timeout=900)
        if r.returncode != 0 or not report.exists():
            raise RuntimeError(tr("pip paket planı alınamadı (kurulum.log)"))
        data = json.loads(report.read_text(encoding="utf-8"))
        items = []
        for it in data.get("install", []):
            url = (it.get("download_info") or {}).get("url")
            md = it.get("metadata") or {}
            if url:
                items.append({"name": md.get("name", "?"), "version": md.get("version", ""), "url": url})
        return items

    def step_packages(self) -> None:
        key = "packages"
        flag = self.rt / ".paketler-tamam"
        if flag.exists():
            self.dones[key] = self.totals[key]; self.step_state.emit(key, "done", self.dones[key], self.totals[key]); return
        self.step_state.emit(key, "running", 0, self.totals[key])
        wheels = self.dl_dir / "paketler"; wheels.mkdir(parents=True, exist_ok=True)
        group_done_bytes = 0
        for gname, reqs, extra in PACKAGE_GROUPS:
            gflag = self.rt / f".paket-{gname}-tamam"
            if gflag.exists():
                continue
            self.message.emit(tr("{gname}: paket listesi çözülüyor…", gname=gname))
            items = self._resolve(reqs, extra)
            self._check_cancel()
            # boyutlar
            for it in items:
                # pip'in verdiği URL'de sürüm eki (+cu126 gibi) %2B olarak kodlanmış olabilir;
                # çözülmezse dosya adı tekerlek (wheel) biçimine uymaz ve pip --find-links onu
                # tanımaz ("Could not find a version that satisfies the requirement torch").
                it["size"] = head_size(it["url"]); it["file"] = wheels / unquote(it["url"].split("/")[-1].split("#")[0])
            group_total = sum(it["size"] for it in items)
            self.totals[key] = max(self.totals[key], group_done_bytes + group_total) if group_total else self.totals[key]
            self.message.emit(tr("{gname}: {n} paket, {mb} MB indiriliyor…",
                                 gname=gname, n=len(items), mb=f"{group_total / 1024**2:,.0f}".replace(",", ".")))
            base = group_done_bytes
            for it in items:
                self._check_cancel()
                download(it["url"], it["file"], self._on_dl(key), self.cancel, expected_size=it["size"],
                         base_done=base, base_total=self.totals[key])
                base += it["size"] or (it["file"].stat().st_size if it["file"].exists() else 0)
            group_done_bytes = base
            self.message.emit(tr("{gname}: kuruluyor (birkaç dakika sürebilir)…", gname=gname))
            r = self._run([self.py, "-m", "pip", "install", "--no-index", "--find-links", wheels,
                           "--no-warn-script-location", *reqs], timeout=5400)
            if r.returncode != 0:
                raise RuntimeError(tr("{gname} paketleri kurulamadı (kurulum.log)", gname=gname))
            gflag.write_text("ok", encoding="utf-8")
        flag.write_text("ok", encoding="utf-8")
        self.dones[key] = self.totals[key]
        self.step_state.emit(key, "done", self.dones[key], self.totals[key])
        self._emit_overall()
        shutil.rmtree(wheels, ignore_errors=True)   # 2+ GB tekerlek dosyası artık gereksiz

    def step_models(self) -> None:
        key = "models"
        mdir = models_cache_dir()
        flag = mdir / ".docon-tamam"
        if flag.exists():
            self.dones[key] = self.totals[key]; self.step_state.emit(key, "done", self.dones[key], self.totals[key]); return
        self.step_state.emit(key, "running", 0, self.totals[key])
        self.message.emit(tr("surya modelleri indiriliyor (marker kendisi indirir, ilerleme klasör boyutundan izlenir)…"))
        code = "from marker.models import create_model_dict; create_model_dict(); print('MODELLER_OK')"
        attempt = 0
        while True:
            attempt += 1
            self._check_cancel()
            with open(self.log_path, "a", encoding="utf-8", errors="replace") as f:
                self._proc = subprocess.Popen([str(self.py), "-c", code], stdout=f, stderr=subprocess.STDOUT,
                                              creationflags=NO_WINDOW, cwd=str(self.rt),
                                              env={**os.environ, "PYTHONIOENCODING": "utf-8"})
                meter = SpeedMeter()
                while self._proc.poll() is None:
                    if self.cancel.is_set():
                        self._kill(); raise InstallCancelled()
                    size = _dir_size(mdir)
                    self.dones[key] = min(size, self.totals[key]) if self.totals[key] else size
                    if size > self.totals[key]:
                        self.totals[key] = size
                    spd = meter.add(size)
                    rem = self.totals[key] - size
                    self.step_state.emit(key, "running", size, self.totals[key])
                    self._emit_overall(spd, rem / spd if spd > 0 and rem > 0 else None)
                    time.sleep(1.0)
                rc = self._proc.returncode; self._proc = None
            if rc == 0:
                break
            if attempt >= MODEL_RETRIES:
                raise RuntimeError(tr("Modeller {n} denemede indirilemedi. İnternet bağlantısını kontrol edip 'Yeniden dene'ye bas.", n=attempt))
            self.message.emit(tr("Model indirme kesildi, {n}. yeniden deneme (tamamlanan dosyalar korunur)…", n=attempt))
            for _ in range(50):
                self._check_cancel(); time.sleep(0.2)
        mdir.mkdir(parents=True, exist_ok=True)
        flag.write_text("ok", encoding="utf-8")
        self.totals[key] = self.dones[key] = max(_dir_size(mdir), 1)
        self.step_state.emit(key, "done", self.dones[key], self.totals[key])
        self._emit_overall()

    def step_verify(self) -> str:
        key = "verify"
        self.step_state.emit(key, "running", 0, 0)
        self.message.emit(tr("Kurulum doğrulanıyor…"))
        out = app_data_dir() / "dogrulama.txt"
        code = ("import torch, marker, pypdf, scipy, pypdfium2, json;"
                "print(json.dumps({'cuda': torch.cuda.is_available(), 'gpu': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,"
                "'torch': torch.__version__, 'scipy': scipy.__version__}))")
        r = subprocess.run([str(self.py), "-c", code], capture_output=True, text=True, timeout=300, creationflags=NO_WINDOW)
        if r.returncode != 0:
            self._log(r.stdout + r.stderr)
            raise RuntimeError(tr("Doğrulama başarısız: paketler içe aktarılamadı (kurulum.log)"))
        info = json.loads(r.stdout.strip().splitlines()[-1])
        out.write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
        self.step_state.emit(key, "done", 0, 0)
        if info.get("cuda"):
            return tr("Kurulum tamam. GPU: {gpu} · torch {v}", gpu=info.get('gpu'), v=info.get('torch'))
        return tr("Kurulum tamam, ancak CUDA bulunamadı; dönüştürme CPU'da çok yavaş olur. torch {v}", v=info.get('torch'))

    # ---------- ana döngü ----------
    def run(self) -> None:
        try:
            if os.environ.get("DOCON_SIMULE") == "1":
                self._simulate(); return
            self.step_python()
            self.step_packages()
            self.step_models()
            msg = self.step_verify()
            self.message.emit(msg)
            self.finished_ok.emit()
        except (InstallCancelled, DownloadCancelled):
            self._log("kullanıcı duraklattı")
            self.paused.emit()
        except (DownloadError, RuntimeError, OSError, zipfile.BadZipFile) as e:
            self._log(f"HATA: {e}")
            self.failed.emit(str(e))
        except Exception as e:  # beklenmeyen
            self._log(f"BEKLENMEYEN HATA: {e!r}")
            self.failed.emit(tr("Beklenmeyen hata: {e}", e=e))

    def _simulate(self) -> None:
        """Geliştirme benzetimi: gerçek indirme yok, arayüz akışı denenir."""
        sn = float(os.environ.get("DOCON_SIMULE_SN", "1.5"))
        for k, _t, total in SETUP_STEPS:
            self.step_state.emit(k, "running", 0, total)
            steps = 20
            for i in range(1, steps + 1):
                if self.cancel.is_set():
                    self.paused.emit(); return
                time.sleep(sn / steps)
                self.dones[k] = int(total * i / steps)
                self.step_state.emit(k, "running", self.dones[k], total)
                self._emit_overall(38.4 * 1024**2, None)
            self.step_state.emit(k, "done", total, total)
        self.message.emit(tr("Benzetim: kurulum tamam."))
        self.finished_ok.emit()


def _dir_size(d: Path) -> int:
    if not d.exists():
        return 0
    total = 0
    for root, _dirs, files in os.walk(d):
        for n in files:
            try:
                total += os.path.getsize(os.path.join(root, n))
            except OSError:
                pass
    return total
