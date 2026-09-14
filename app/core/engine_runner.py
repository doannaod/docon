"""Motoru (engine/kosucu.py) programın çalışma ortamındaki Python ile ayrı süreçte çalıştırır,
JSON olaylarını Qt sinyallerine çevirir. Durdurma: süreç ağacı kapatılır; biten bloklar
durum.json sayesinde korunur (talimat 4.4).
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, Signal

from app.core.i18n import tr
from app.core.paths import install_dir, logs_dir

HAM_KLASOR = "_ham-ocr"
TEST_KLASOR = "_test-kosusu"


def kosucu_path() -> Path:
    return install_dir() / "engine" / "kosucu.py"


class ConversionRunner(QObject):
    blocks = Signal(int, int)             # toplam sayfa, toplam blok
    block_started = Signal(int, int, int)  # k, sayfa a, sayfa b
    block_skipped = Signal(int)
    block_done = Signal(int, int)          # k, saniye
    block_failed = Signal(int, int)        # k, rc
    stage = Signal(int)                    # 1 OCR, 2 bölme
    outline = Signal(bool, int, int)       # var mı, bölüm, ek (yoksa parça boyutu ek'te)
    file_written = Signal(str)
    log = Signal(str)
    finished = Signal(dict)                # {"bolum","ek","sekil","bayt","tam"}
    test_finished = Signal(dict)           # test koşusu özeti (kosucu.test_ozeti)
    failed = Signal(str)
    stopped = Signal()

    def __init__(self, python: Path, pdf: str, output_dir: str, force_ocr: bool, parent=None,
                 test_pages: int | None = None, block_size: int | None = None, chunk_size: int | None = None,
                 title: str | None = None):
        super().__init__(parent)
        self.python = python
        self.pdf = Path(pdf)
        self.output_dir = Path(output_dir)
        self.force_ocr = force_ocr
        self.test_pages = test_pages
        self.block_size = block_size
        self.chunk_size = chunk_size
        self.title = title or self.pdf.stem
        self.log_path = logs_dir() / f"{self.pdf.stem}-{time.strftime('%Y%m%d-%H%M%S')}.log"
        self._proc: QProcess | None = None
        self._buffer = ""
        self._stopping = False
        self._result: dict | None = None

    # --- yaşam döngüsü ---
    def start(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        ham = self.output_dir / (TEST_KLASOR if self.test_pages else HAM_KLASOR)
        args = [
            str(kosucu_path()),
            "--pdf", str(self.pdf),
            "--ham", str(ham),
            "--hedef", str(self.output_dir),
            "--force-ocr", "1" if self.force_ocr else "0",
            "--baslik", f"*{self.title}*",
            "--log", str(self.log_path),
        ]
        if self.test_pages:
            args += ["--test", str(self.test_pages)]
        if self.block_size:
            args += ["--blok", str(self.block_size)]
        if self.chunk_size:
            args += ["--parca", str(self.chunk_size)]
        p = QProcess(self)
        p.setProgram(str(self.python))
        p.setArguments(args)
        p.setWorkingDirectory(str(self.output_dir))
        p.setProcessChannelMode(QProcess.SeparateChannels)
        p.readyReadStandardOutput.connect(self._on_stdout)
        p.readyReadStandardError.connect(self._on_stderr)
        p.finished.connect(self._on_finished)
        p.errorOccurred.connect(self._on_error)
        self._proc = p
        p.start()

    def stop(self) -> None:
        if not self._proc or self._proc.state() == QProcess.NotRunning:
            return
        self._stopping = True
        pid = int(self._proc.processId())
        if sys.platform.startswith("win") and pid:
            # marker alt-süreçleri de dahil tüm ağacı kapat
            subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        else:
            self._proc.kill()

    def is_running(self) -> bool:
        return bool(self._proc) and self._proc.state() != QProcess.NotRunning

    # --- olaylar ---
    def _on_stdout(self) -> None:
        data = bytes(self._proc.readAllStandardOutput()).decode("utf-8", errors="replace")
        self._buffer += data
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split("\n", 1)
            line = line.strip()
            if line:
                self._handle(line)

    def _on_stderr(self) -> None:
        data = bytes(self._proc.readAllStandardError()).decode("utf-8", errors="replace").strip()
        if data:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(data + "\n")

    def _handle(self, line: str) -> None:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            self.log.emit(line); return
        t = ev.get("t")
        if t == "bloklar":
            self.blocks.emit(ev["n"], ev["m"])
        elif t == "blok_basla":
            self.block_started.emit(ev["k"], ev["a"], ev["b"])
        elif t == "blok_atla":
            self.block_skipped.emit(ev["k"])
        elif t == "blok_tamam":
            self.block_done.emit(ev["k"], ev["sn"])
        elif t == "blok_hata":
            self.block_failed.emit(ev["k"], ev["rc"])
        elif t == "asama":
            self.stage.emit(ev["n"])
        elif t == "outline":
            self.outline.emit(True, ev["bolum"], ev["ek"])
        elif t == "outline_yok":
            self.outline.emit(False, 0, ev["parca"])
        elif t == "dosya":
            self.file_written.emit(ev["ad"])
        elif t == "sonuc":
            self._result = ev
        elif t == "test_sonuc":
            self._result = ev
            self._is_test = True
        elif t == "hata":
            self.failed.emit(ev.get("msg", "Bilinmeyen hata"))
        elif t == "log":
            self.log.emit(ev.get("msg", ""))

    def _on_finished(self, code: int, _status) -> None:
        if self._stopping:
            self.stopped.emit()
        elif self._result is not None:
            if getattr(self, "_is_test", False):
                self.test_finished.emit(self._result)
            else:
                self.finished.emit(self._result)
        elif code != 0:
            self.failed.emit(tr("Motor {code} koduyla kapandı. Ayrıntı: {log}", code=code, log=self.log_path.name))

    def _on_error(self, err) -> None:
        if not self._stopping:
            self.failed.emit(tr("Motor başlatılamadı ({err}). Python: {py}", err=err, py=self.python))
