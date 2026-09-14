"""Programın kullandığı klasörler.

- Kurulum klasörü: çalıştırılabilir dosyanın yanı (PyInstaller) ya da proje kökü (geliştirme).
- Varsayılan çıktı: kurulum klasörü içinde `Cikti` (talimat 3.7). Yazılamıyorsa
  %LOCALAPPDATA%\\Docon\\Cikti kullanılır.
- Model önbelleği: marker'ın kendi yeri, %LOCALAPPDATA%\\datalab\\datalab\\Cache\\models (talimat 2).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_DIR_NAME = "Docon"


def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def install_dir() -> Path:
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def app_icon_path() -> Path:
    """Uygulama simgesi (kitap ikonu). Paketle birlikte gelir, `app/assets/icon.ico`."""
    return Path(__file__).resolve().parents[1] / "assets" / "icon.ico"


def app_data_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    p = base / APP_DIR_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def runtime_dir() -> Path:
    """Programın ilk açılışta kurduğu özel Python ortamı (torch + marker)."""
    return app_data_dir() / "runtime"


def models_cache_dir() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    return base / "datalab" / "datalab" / "Cache" / "models"


def history_file() -> Path:
    return app_data_dir() / "gecmis.json"


def logs_dir() -> Path:
    p = app_data_dir() / "loglar"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _writable(p: Path) -> bool:
    try:
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".yazma-testi"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def default_output_root() -> Path:
    preferred = install_dir() / "Cikti"
    if _writable(preferred):
        return preferred
    fallback = app_data_dir() / "Cikti"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def default_output_dir_for(pdf_path: Path) -> Path:
    return default_output_root() / pdf_path.stem


def folder_size_bytes(folder: Path) -> int:
    total = 0
    if not folder.exists():
        return 0
    for root, _dirs, files in os.walk(folder):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                pass
    return total


def format_bytes(n: int | float) -> str:
    """68_400_000 -> '68,4 MB' (Türkçe ondalık virgül)."""
    n = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            if unit == "B":
                return f"{int(n)} B"
            return f"{n:.1f}".replace(".", ",") + f" {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def open_in_explorer(folder: Path) -> None:
    folder = Path(folder)
    if sys.platform.startswith("win"):
        os.startfile(str(folder))  # type: ignore[attr-defined]
    else:  # geliştirme kolaylığı
        import subprocess

        subprocess.Popen(["xdg-open", str(folder)])
