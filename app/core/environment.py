"""Çalışma ortamı durumu: özel Python ortamı (torch + marker) ve surya modelleri kurulu mu?

İndirme ve kurulumun kendisi (talimat 3.8, 4.0–4.2) bir sonraki adımda `installer.py` içinde
yazılacak; bu modül yalnızca durum tespiti yapar ve kurulum adımlarını tanımlar.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.core.i18n import tr
from app.core.paths import models_cache_dir, runtime_dir

MARKER_VERSION = "1.10.2"
TORCH_INDEX = "https://download.pytorch.org/whl/cu126"

# Kurulum adımları: (anahtar, kullanıcıya görünen ad, yaklaşık boyut)
# Boyutlar gerçek bir kurulumdan ölçüldü: packages = indirilen paket dosyalarının
# toplamı (torch dahil, kurulum sonrası silinir); models = %LOCALAPPDATA%\datalab\datalab\Cache\models
# klasörünün gerçek boyutu.
SETUP_STEPS = [
    ("python", tr("Python çalışma ortamı"), 28 * 1024**2),
    ("packages", tr("torch (CUDA 12.6) ve marker-pdf {v}", v=MARKER_VERSION), 2_763 * 1024**2),
    ("models", tr("surya modelleri: metin tespiti, tanıma, düzen, tablo"), 3_290 * 1024**2),
    ("verify", tr("Kurulum doğrulaması"), 0),
]


@dataclass
class EnvironmentStatus:
    runtime_python: Path | None
    packages_ok: bool
    models_ok: bool
    gpu_name: str | None

    @property
    def ready(self) -> bool:
        return self.runtime_python is not None and self.packages_ok and self.models_ok

    @property
    def gpu_label(self) -> str:
        return f"GPU: {self.gpu_name}" if self.gpu_name else tr("GPU bulunamadı (CPU, yavaş)")


def runtime_python() -> Path | None:
    p = runtime_dir() / "python.exe"
    return p if p.exists() else None


def packages_installed(py: Path) -> bool:
    try:
        out = subprocess.run(
            [str(py), "-c", "import marker, torch; print(torch.cuda.is_available())"],
            capture_output=True, text=True, timeout=120,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return out.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def models_present() -> bool:
    d = models_cache_dir()
    if not d.exists():
        return False
    # marker/surya her modeli kendi klasörüne indirir; en az bir tamamlanmış klasör beklenir
    marker_file = d / ".docon-tamam"
    return marker_file.exists()


def detect_gpu() -> str | None:
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip().splitlines()[0]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return None


def check_environment(deep: bool = True) -> EnvironmentStatus:
    """deep=True (varsayılan): işaret dosyasına güvenmez, paketleri gerçekten içe aktarmayı dener
    (Kapsam v2: kullanıcı runtime klasörünü silmişse program yanılmasın)."""
    py = runtime_python()
    flag = (runtime_dir() / ".paketler-tamam").exists()
    pk = bool(py) and flag and (packages_installed(py) if deep else True)
    if bool(py) and flag and not pk:
        # işaret var ama içe aktarma başarısız: işareti kaldır ki kurulum adımı yeniden çalışsın
        try:
            (runtime_dir() / ".paketler-tamam").unlink()
        except OSError:
            pass
    return EnvironmentStatus(runtime_python=py, packages_ok=pk, models_ok=models_present(), gpu_name=detect_gpu())
