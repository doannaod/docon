"""Ana pencere (Kapsam v2): sol menü + sayfa yığını; kuyruk, kurulum ve çeviri akışını yönetir."""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup, QFileDialog, QHBoxLayout, QInputDialog, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from app import APP_NAME, __version__
from app.core.analyzer import PdfAnalysis, analyze_pdf
from app.core.engine_runner import ConversionRunner
from app.core.environment import MARKER_VERSION, SETUP_STEPS, EnvironmentStatus
from app.core.history import HistoryStore, JobRecord, format_duration
from app.core.i18n import tr
from app.core.installer import InstallWorker
from app.core.paths import app_icon_path, default_output_root, folder_size_bytes, open_in_explorer
from app.core.queue import BookItem, BookQueue
from app.core.quality import scan as quality_scan
from app.core.settings import Settings
from app.core.system import GpuMonitor, clean_raw_dirs, find_raw_dirs, keep_awake, preflight
from app.core.update_check import RELEASES_URL
from app.core.workers import AnalyzeWorker, EnvironmentCheckWorker, UpdateCheckWorker
from app.ui import theme
from app.ui.pages.convert import ConvertPage
from app.ui.pages.done import DonePage
from app.ui.pages.history import HistoryPage
from app.ui.pages.home import HomePage
from app.ui.pages.settings import SettingsPage
from app.ui.pages.setup import SetupPage, SetupStep
from app.ui.widgets import label, svg_icon

SIMULE = os.environ.get("DOCON_SIMULE") == "1"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        # Pencere yeniden boyutlandırılabilir (kullanıcı kararı). Küçülünce/bir kutunun
        # içeriği büyüyünce taşma olmasın diye sayfalar artık kendi içinde kaydırılabilir
        # (bkz. app/ui/widgets.py scroll_body — Ayarlar ve Bitti sayfalarında kullanılıyor).
        self.resize(1100, 700)
        self.setMinimumSize(900, 560)
        icon_path = app_icon_path()
        self.setWindowIcon(QIcon(str(icon_path)) if icon_path.exists() else svg_icon("file", theme.ACCENT, 32, 1.8))
        self.settings = Settings()
        self.history = HistoryStore()
        self.queue = BookQueue()
        self.env: EnvironmentStatus | None = None
        self._runner: ConversionRunner | None = None
        self._installer: InstallWorker | None = None
        self._job: JobRecord | None = None
        self._book: BookItem | None = None
        self._run_mode: str | None = None          # "test" | "full"
        self._batch: list[str] = []                # sıradaki kitap id'leri
        self._batch_index = 0
        self._batch_done: list[str] = []
        self._pending_analysis: list[str] = []
        self._analyze_worker: AnalyzeWorker | None = None
        self._tick_timer = QTimer(self); self._tick_timer.setInterval(1000); self._tick_timer.timeout.connect(self._tick)
        self.gpu = GpuMonitor(parent=self)
        self.tray = QSystemTrayIcon(self.windowIcon(), self); self.tray.setToolTip(APP_NAME)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray.show()

        central = QWidget(); self.setCentralWidget(central)
        outer = QHBoxLayout(central); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        # Kenar çubuğu
        side = QWidget(); side.setObjectName("Sidebar"); side.setFixedWidth(200)
        sl = QVBoxLayout(side); sl.setContentsMargins(12, 16, 12, 16); sl.setSpacing(4)
        self.nav_home = QPushButton("  " + tr("Ana Sayfa")); self.nav_home.setIcon(svg_icon("home", theme.ACCENT_DARK))
        self.nav_hist = QPushButton("  " + tr("Geçmiş İşler")); self.nav_hist.setIcon(svg_icon("clock", theme.TEXT_SOFT))
        self.nav_set = QPushButton("  " + tr("Ayarlar")); self.nav_set.setIcon(svg_icon("gear", theme.TEXT_SOFT))
        group = QButtonGroup(self); group.setExclusive(True)
        for b in (self.nav_home, self.nav_hist, self.nav_set):
            b.setCheckable(True); b.setCursor(Qt.PointingHandCursor); group.addButton(b)
        sl.addWidget(self.nav_home); sl.addWidget(self.nav_hist); sl.addStretch(); sl.addWidget(self.nav_set)
        self.side_footer = label(tr("Ortam denetleniyor…"), "SidebarFooter", wrap=True)
        sl.addWidget(self.side_footer)
        outer.addWidget(side)

        # Sayfalar
        self.stack = QStackedWidget(); outer.addWidget(self.stack, 1)
        self.home = HomePage(); self.setup = SetupPage(); self.convert = ConvertPage()
        self.done = DonePage(); self.hist = HistoryPage(); self.settings_page = SettingsPage(self.settings)
        for p in (self.home, self.setup, self.convert, self.done, self.hist, self.settings_page):
            self.stack.addWidget(p)

        # Bağlantılar
        self.nav_home.clicked.connect(self.go_home)
        self.nav_hist.clicked.connect(self.go_history)
        self.nav_set.clicked.connect(self.go_settings)
        self.home.files_added.connect(self.on_files_added)
        self.home.book_selected.connect(self.on_book_selected)
        self.home.rename_requested.connect(self.on_rename)
        self.home.change_file_requested.connect(self.on_change_file)
        self.home.remove_requested.connect(self.on_remove)
        self.home.reordered.connect(self.queue.reorder)
        self.home.force_ocr_changed.connect(self.on_force_ocr)
        self.home.output_root_changed.connect(self.on_output_root)
        self.home.test_requested.connect(self.on_test)
        self.home.start_all_requested.connect(self.on_start_all)
        self.home.recent_open_requested.connect(self.on_open_recent)
        self.home.open_output_requested.connect(self.on_open_output)
        self.home.show_history.connect(self.go_history)
        self.hist.resume_requested.connect(self.on_resume)
        self.hist.open_log_requested.connect(self.on_open_log)
        self.convert.stop_requested.connect(self.on_stop)
        self.convert.skip_requested.connect(self.on_skip)
        self.done.new_book.connect(self.go_home)
        self.setup.start_requested.connect(self._start_install)
        self.setup.later_requested.connect(self.go_home)
        self.setup.pause_requested.connect(self._on_setup_pause)
        self.setup.resume_requested.connect(self._start_install)
        self.setup.retry_requested.connect(self._start_install)
        self.settings_page.clean_requested.connect(self.on_clean_raw)
        self.settings_page.changed.connect(self._on_settings_changed)
        self.gpu.sample.connect(self.convert.gpu.update_sample)

        self.home.set_test_pages(self.settings.test_pages)
        self.go_home()
        QTimer.singleShot(0, self._startup)

    # ====================== açılış ======================
    def _startup(self) -> None:
        self._update_tag: str | None = None
        self._env_worker = EnvironmentCheckWorker(self)
        self._env_worker.finished_with.connect(self._on_env)
        self._env_worker.start()
        self._update_worker = UpdateCheckWorker(__version__, self)
        self._update_worker.finished_with.connect(self._on_update_check)
        self._update_worker.start()

    def _on_env(self, status: EnvironmentStatus) -> None:
        self.env = status
        ready = status.ready
        self.side_footer.setText((tr("Program hazır") if ready else tr("İlk kurulum bekliyor")) + f"\n{status.gpu_label}")
        self.convert.gpu.set_gpu_available(self.gpu.available)
        self._refresh_about()
        if not ready and not getattr(self, "_setup_shown", False):
            self._setup_shown = True
            self._show_setup_consent()

    def _on_update_check(self, tag: str | None) -> None:
        self._update_tag = tag
        self._refresh_about()
        if tag and self.tray.isVisible():
            self.tray.showMessage(APP_NAME, tr("Yeni sürüm mevcut: {tag}. Ayarlar'dan indirme sayfasını açabilirsin.", tag=tag),
                                  QSystemTrayIcon.Information, 8000)

    def _refresh_about(self) -> None:
        gpu_label = self.env.gpu_label if self.env else "…"
        update_text = tr("Yeni sürüm mevcut: {tag}", tag=self._update_tag) if self._update_tag else ""
        self.settings_page.set_about(f"marker-pdf {MARKER_VERSION} · {gpu_label}", update_text)

    # ====================== gezinme ======================
    def go_home(self) -> None:
        self.home.set_books(self.queue.items)
        self.home.set_recent(self.history.completed())
        self.nav_home.setChecked(True)
        self.stack.setCurrentWidget(self.home)

    def go_history(self) -> None:
        self.hist.set_jobs(self.history.all())
        self.nav_hist.setChecked(True)
        self.stack.setCurrentWidget(self.hist)

    def go_settings(self) -> None:
        self.settings_page.load()
        dirs = find_raw_dirs([Path(j.output_dir) for j in self.history.completed()])
        self.settings_page.set_clean_info(len(dirs), sum(folder_size_bytes(d) for d in dirs))
        self.nav_set.setChecked(True)
        self.stack.setCurrentWidget(self.settings_page)

    def _on_settings_changed(self) -> None:
        self.home.set_test_pages(self.settings.test_pages)

    # ====================== kuyruk ======================
    def _output_root(self) -> str:
        return str(self.settings.last_output_root or default_output_root())

    def on_files_added(self, paths: list[str]) -> None:
        added = []
        for p in paths:
            b = self.queue.add(p, self._output_root())
            if b:
                added.append(b)
        self.home.set_books(self.queue.items)
        for b in added:
            self._pending_analysis.append(b.id)
        self._analyze_next()
        if added:
            self.home.list.setCurrentRow(self.queue.items.index(added[0]))

    def _analyze_next(self) -> None:
        if self._analyze_worker and self._analyze_worker.isRunning():
            return
        while self._pending_analysis:
            bid = self._pending_analysis.pop(0)
            b = self.queue.get(bid)
            if b and not b.analysis:
                self._analyze_worker = AnalyzeWorker(b.pdf_path, self)
                self._analyze_worker.finished_with.connect(lambda a, bid=bid: self._on_analysis(bid, a))
                self._analyze_worker.start()
                return

    def _on_analysis(self, bid: str, a: PdfAnalysis) -> None:
        b = self.queue.get(bid)
        if b:
            b.page_count = a.page_count
            b.analysis = {
                "is_scanned": a.is_scanned, "text_is_broken": a.text_is_broken, "recommend_force_ocr": a.recommend_force_ocr,
                "text_layer_label": a.text_layer_label, "kind_label": a.kind_label, "outline_label": a.outline_label,
                "has_outline": a.has_outline, "outline_count": a.outline_count, "reason": a.reason, "error": a.error,
            }
            self.queue.save()
            self.home.refresh_book(b)
            self._refresh_preflight(b)
        self._analyze_next()

    def on_book_selected(self, bid: str) -> None:
        b = self.queue.get(bid)
        if b:
            self._refresh_preflight(b)

    def _refresh_preflight(self, b: BookItem) -> None:
        pf = preflight(b.output_dir, b.size_bytes, install_needed=not (self.env and self.env.ready))
        gpu = tr("GPU: {name}, {gb} GB", name=pf.gpu.name, gb=f"{pf.gpu.mem_total_mb / 1024:.0f}") if pf.gpu and pf.gpu.mem_total_mb else tr("GPU yok")
        text = tr("Disk: {free} GB boş, ~{need} GB gerekir · {gpu}",
                  free=f"{pf.disk_free_gb:.0f}", need=f"{pf.disk_need_gb:.1f}", gpu=gpu).replace(".", ",")
        warns = [w.lstrip("! ") for w in pf.warnings]
        if warns:
            text += " · " + " ".join(warns)
        else:
            text += " · " + tr("Hazır")
        self.home.set_preflight(text, warn=bool(warns))

    def on_rename(self, bid: str) -> None:
        b = self.queue.get(bid)
        if not b:
            return
        name, ok = QInputDialog.getText(self, tr("Kitabın adı"), tr("Bu ad hem listede hem çıktı klasöründe kullanılır:"), text=b.title)
        if ok and name.strip():
            b.title = name.strip()[:80]; self.queue.save(); self.home.refresh_book(b)

    def on_change_file(self, bid: str) -> None:
        b = self.queue.get(bid)
        if not b:
            return
        path, _ = QFileDialog.getOpenFileName(self, tr("PDF seç"), str(Path(b.pdf_path).parent), tr("PDF dosyaları (*.pdf)"))
        if path:
            b.pdf_path = path; b.size_bytes = Path(path).stat().st_size; b.analysis = None; b.test = None
            b.status = "bekliyor"; b.page_count = 0
            self.queue.save(); self.home.refresh_book(b)
            self._pending_analysis.append(bid); self._analyze_next()

    def on_remove(self, bid: str) -> None:
        self.queue.remove(bid)
        self.home.set_books(self.queue.items, keep_selection=False)

    def on_force_ocr(self, bid: str, value) -> None:
        b = self.queue.get(bid)
        if b:
            b.force_ocr = value; self.queue.save(); self.home.refresh_book(b)

    def on_output_root(self, bid: str, root: str) -> None:
        self.settings.last_output_root = root
        for b in self.queue.items:
            if b.status in ("bekliyor", "test-tamam"):
                b.output_root = root
        self.queue.save()
        b = self.queue.get(bid)
        if b:
            self.home.refresh_book(b); self._refresh_preflight(b)

    def on_open_recent(self, job_id: str) -> None:
        j = self.history.get(job_id)
        if not j:
            return
        p = Path(j.output_dir)
        if p.exists():
            open_in_explorer(p)
        else:
            QMessageBox.warning(self, APP_NAME, tr("Dosya yolu değişmiş.\n\nKitap klasörü artık burada değil:\n{p}\n\nTaşındıysa yeni yerinden açabilirsin; geçmiş kaydı eski yolu gösterir.", p=j.output_dir))

    def on_open_output(self, book_id: str) -> None:
        b = self.queue.get(book_id)
        if not b:
            return
        p = b.output_dir
        if p.exists():
            open_in_explorer(p)
        else:
            QMessageBox.warning(self, APP_NAME, tr("Klasör bulunamadı:\n{p}", p=p))

    # ====================== kurulum ======================
    def _env_ready(self) -> bool:
        return bool(self.env and (self.env.ready or SIMULE))

    def _show_setup_consent(self) -> None:
        pf = preflight(Path(self._output_root()), 0, install_needed=True)
        gpu = tr("GPU: {name}", name=pf.gpu.name) if pf.gpu else tr("NVIDIA GPU bulunamadı (çok yavaş çalışır)")
        text = tr("C: sürücüsü {free} GB boş, 12 GB gerekir · {gpu}", free=f"{pf.disk_free_gb:.0f}", gpu=gpu)
        self.setup.show_consent(text, sum(b for _, _, b in SETUP_STEPS) / 1024**3)
        self._setup_steps = {k: SetupStep(k, t, total_bytes=b) for k, t, b in SETUP_STEPS}
        self.setup.set_steps(list(self._setup_steps.values()))
        self.nav_home.setChecked(True)
        self.stack.setCurrentWidget(self.setup)

    def _start_install(self) -> None:
        if self._installer and self._installer.isRunning():
            return
        self.settings.install_consented = True
        self.setup.show_progress()
        self.setup.update_progress(0.0, None, None, 0, sum(b for _, _, b in SETUP_STEPS))
        self.setup.set_banner(tr("Bağlantı koparsa indirme kaldığı yerden devam eder."))
        w = InstallWorker(self)
        w.step_state.connect(self._on_install_step)
        w.progress.connect(lambda f, s, e, d, t: self.setup.update_progress(f, s or None, e, int(d), int(t)))
        w.message.connect(lambda m: self.setup.set_banner(m))
        w.finished_ok.connect(self._on_install_done)
        w.failed.connect(lambda m: self.setup.set_banner(tr("Kurulum durdu: {m}", m=m), error=True))
        w.paused.connect(lambda: self.setup.set_banner(tr("Duraklatıldı. 'Devam et' ile kaldığı yerden sürer.")))
        self._installer = w
        self.setup.retry.hide()
        keep_awake(True)
        w.start()

    def _on_setup_pause(self) -> None:
        if self._installer and self._installer.isRunning():
            self._installer.cancel.set()

    def _on_install_step(self, key: str, state: str, done: float, total: float) -> None:
        s = self._setup_steps.get(key)
        if s:
            s.state = state; s.done_bytes = int(done)
            if total:
                s.total_bytes = int(total)
            self.setup.update_step(s)

    def _on_install_done(self) -> None:
        keep_awake(False)
        self.setup.set_banner(tr("Kurulum tamamlandı. Program kullanıma hazır."))
        self._notify(tr("Program kullanıma hazır"), tr("Gereken yazılım ve modeller indi. Artık kitap ekleyip çevirebilirsin."))
        self._env_worker = EnvironmentCheckWorker(self)
        self._env_worker.finished_with.connect(self._after_install_env)
        self._env_worker.start()

    def _after_install_env(self, status: EnvironmentStatus) -> None:
        self._on_env(status)
        if status.ready or SIMULE:
            if SIMULE and not status.ready:
                self.env = EnvironmentStatus(runtime_python=Path(sys.executable), packages_ok=True, models_ok=True, gpu_name=tr("Benzetim"))
            QMessageBox.information(self, APP_NAME, tr("Kurulum tamamlandı. Program kullanıma hazır.\nKitap eklemek için Ana Sayfa'ya dönülüyor."))
            self.go_home()
        else:
            self.setup.set_banner(tr("Kurulum bitti görünüyor ama ortam denetimi geçemedi. 'Yeniden dene' ile tekrar kontrol edilir."), error=True)

    # ====================== çeviri akışı ======================
    def on_test(self, bid: str) -> None:
        if not self._env_ready():
            self._show_setup_consent(); return
        self._batch = [bid]; self._batch_index = 0; self._batch_done = []
        self._run_mode = "test-only"
        self._run_book(self.queue.get(bid), mode="test")

    def on_start_all(self) -> None:
        if not self._env_ready():
            self._show_setup_consent(); return
        pend = self.queue.pending()
        if not pend:
            return
        self._batch = [b.id for b in pend]; self._batch_index = 0; self._batch_done = []
        self._run_mode = "batch"
        self._run_next()

    def on_resume(self, job_id: str) -> None:
        job = self.history.get(job_id)
        if not job:
            return
        if not Path(job.pdf_path).exists():
            QMessageBox.warning(self, APP_NAME, tr("PDF bulunamadı:\n{p}", p=job.pdf_path)); return
        if not self._env_ready():
            self._show_setup_consent(); return
        b = next((x for x in self.queue.items if x.job_id == job.id), None)
        if not b:
            b = self.queue.add(job.pdf_path, str(Path(job.output_dir).parent))
            if b is None:
                b = next(x for x in self.queue.items if x.pdf_path.lower() == job.pdf_path.lower())
            b.title = job.title or b.title; b.job_id = job.id; b.force_ocr = job.force_ocr; b.page_count = job.page_count
            b.status = "test-tamam"; b.test = b.test or {"md_var": True, "sayfa": 0, "devam": True}
            self.queue.save()
        self._batch = [b.id]; self._batch_index = 0; self._batch_done = []; self._run_mode = "batch"
        self._run_next()

    def _run_next(self) -> None:
        while self._batch_index < len(self._batch):
            b = self.queue.get(self._batch[self._batch_index])
            if b and b.status not in ("bitti", "atlandi"):
                mode = "full" if b.test else "test"
                self._run_book(b, mode); return
            self._batch_index += 1
        self._finish_batch()

    def _run_book(self, b: BookItem | None, mode: str) -> None:
        if not b or not self.env:
            return
        self._book = b
        is_test = mode == "test"
        b.status = "test-suruyor" if is_test else "suruyor"
        self.queue.save(); self.home.refresh_book(b)
        force = b.effective_force_ocr
        if not is_test:
            job = self.history.get(b.job_id) if b.job_id else None
            if job is None:
                job = JobRecord(pdf_path=b.pdf_path, output_dir=str(b.output_dir), force_ocr=force, page_count=b.page_count,
                                input_bytes=b.size_bytes, total_blocks=max(1, -(-b.page_count // self.settings.block_size)),
                                title=b.title)
                self.history.add(job); b.job_id = job.id; self.queue.save()
            job.status = "running"; job.title = b.title; job.force_ocr = force
            self._job = job
        else:
            self._job = None
        self._job_started = time.monotonic()
        self._duration_base = self._job.duration_sec if self._job else 0
        self._block_times: list[float] = []
        self._block_started_at: float | None = None
        self._total_blocks = self._job.total_blocks if self._job else 1
        self._done_blocks = self._job.done_blocks if self._job else 0

        r = ConversionRunner(self.env.runtime_python, b.pdf_path, str(b.output_dir), force, self,
                             test_pages=self.settings.test_pages if is_test else None,
                             block_size=self.settings.block_size, chunk_size=self.settings.chunk_size, title=b.title)
        r.blocks.connect(self._on_blocks); r.block_started.connect(self._on_block_started)
        r.block_skipped.connect(self._on_block_skipped); r.block_done.connect(self._on_block_done)
        r.block_failed.connect(lambda k, rc: self.convert.add_log(tr("Blok {k} hata verdi (kod {rc})", k=k, rc=rc)))
        r.stage.connect(self._on_stage); r.outline.connect(self._on_outline)
        r.file_written.connect(lambda ad: self.convert.add_log(tr("Yazıldı: {ad}", ad=ad)))
        r.log.connect(lambda m: m and self.convert.add_log(m))
        r.finished.connect(self._on_book_finished); r.test_finished.connect(self._on_test_finished)
        r.failed.connect(self._on_book_failed); r.stopped.connect(self._on_stopped)
        self._runner = r
        if self._job:
            self._job.log_path = str(r.log_path); self.history.update(self._job)

        names = [self.queue.get(i).title for i in self._batch if self.queue.get(i)]
        self.convert.begin(b.title, force, self.env.gpu_label, self._total_blocks, self._done_blocks,
                           (b.analysis or {}).get("has_outline"), self._batch_index, len(self._batch), is_test)
        self.convert.gpu.set_queue(names, self._batch_index)
        self.convert.add_log(tr("Motor başlatılıyor…"))
        self.stack.setCurrentWidget(self.convert)
        keep_awake(True); self.gpu.start(); self._tick_timer.start()
        r.start()

    # --- motor olayları ---
    def _on_blocks(self, pages: int, total: int) -> None:
        self._total_blocks = total
        if self._job:
            self._job.page_count = pages; self._job.total_blocks = total; self.history.update(self._job)
        if self._book and not self._book.page_count:
            self._book.page_count = pages
        self.convert.update_blocks(total, self._done_blocks, 0.0, None, None)
        self.convert.add_log(tr("{pages} sayfa, {total} blok", pages=f"{pages:,}".replace(",", "."), total=total))

    def _on_block_started(self, k: int, a: int, b: int) -> None:
        self._block_started_at = time.monotonic(); self._done_blocks = k - 1
        self.convert.update_blocks(self._total_blocks, k - 1, 0.0, a + 1, b + 1)
        self.convert.add_log(tr("Blok {k} için marker başlatıldı (sayfa {a}–{b})", k=k, a=a + 1, b=b + 1))

    def _on_block_skipped(self, k: int) -> None:
        self._done_blocks = max(self._done_blocks, k)
        self.convert.update_blocks(self._total_blocks, self._done_blocks, 0.0, None, None)

    def _on_block_done(self, k: int, sec: int) -> None:
        self._block_times.append(float(sec)); self._block_started_at = None
        self._done_blocks = max(self._done_blocks, k)
        if self._job:
            self._job.done_blocks = self._done_blocks; self.history.update(self._job)
        self.convert.update_blocks(self._total_blocks, self._done_blocks, 0.0, None, None)
        self.convert.add_log(tr("Blok {k} tamamlandı ({sec})", k=k, sec=format_duration(sec)))

    def _on_stage(self, n: int) -> None:
        self.convert.set_stage(n)
        if n == 2:
            self._block_started_at = None
            self.convert.update_blocks(self._total_blocks, self._total_blocks, 0.0, None, None)
            self.convert.add_log(tr("OCR bitti, bölme aşaması başladı"))

    def _on_outline(self, has: bool, chapters: int, other: int) -> None:
        self.convert.add_log(tr("İçindekiler bulundu: {ch} bölüm, {other} ek", ch=chapters, other=other) if has
                             else tr("İçindekiler yok, {other} sayfalık parçalara bölünüyor", other=other))

    def _tick(self) -> None:
        if not self._runner:
            return
        elapsed = time.monotonic() - self._job_started
        avg = sum(self._block_times) / len(self._block_times) if self._block_times else None
        frac = 0.0
        if self._block_started_at is not None and avg:
            frac = min(0.95, (time.monotonic() - self._block_started_at) / avg)
        remaining = max(0, self._total_blocks - self._done_blocks)
        eta = remaining * avg - (frac * avg if self._block_started_at else 0) if avg and remaining else None
        rem_books = max(0, len(self._batch) - self._batch_index - 1)
        rem_eta = None
        if rem_books and avg and self._book and self._book.page_count:
            per_page = avg / max(1, self.settings.block_size)
            rem_eta = sum(per_page * (self.queue.get(i).page_count or self._book.page_count) for i in self._batch[self._batch_index + 1:] if self.queue.get(i))
        self.convert.update_times(elapsed, eta, rem_books, rem_eta)
        if self._block_started_at is not None:
            self.convert.strip.set_state(self._total_blocks, self._done_blocks, frac)
            self.convert.percent.setText(f"{int((self._done_blocks + frac) / max(1, self._total_blocks) * 100)} %")
        if self._job:
            self._job.duration_sec = self._duration_base + int(elapsed)

    def _end_run(self) -> None:
        self._tick_timer.stop(); self.gpu.stop(); keep_awake(False); self._runner = None

    def _on_test_finished(self, r: dict) -> None:
        self._end_run()
        b = self._book
        if b:
            r["sure_sn"] = int(time.monotonic() - self._job_started)
            rec = bool((b.analysis or {}).get("recommend_force_ocr")) or r.get("bos_denklem", 0) > 0 or r.get("bozuk_karakter", 0) > 0
            if r.get("md_var") and r.get("karakter_sayfa", 0) < 200:
                rec = True   # sayfa başına çok az metin: taranmış olabilir
            r["oneri_force_ocr"] = rec
            b.test = r; b.status = "test-tamam"; self.queue.save(); self.home.refresh_book(b)
        if self._run_mode == "test-only":
            self.go_home()
            if b:
                self.home.list.setCurrentRow(self.queue.items.index(b))
            return
        self._run_next()   # aynı kitap: test bitti, tam koşu

    def _on_book_finished(self, r: dict) -> None:
        self._end_run()
        job, b = self._job, self._book
        if job:
            job.status = "done" if r.get("tam", True) else "error"
            job.finished_at = datetime.now().isoformat(timespec="seconds")
            job.done_blocks = job.total_blocks
            job.chapters = r.get("bolum", 0); job.appendices = r.get("ek", 0); job.figures = r.get("sekil", 0)
            job.output_bytes = r.get("bayt", 0) or folder_size_bytes(Path(job.output_dir))
            job.duration_sec = self._duration_base + int(time.monotonic() - self._job_started)
            try:
                job.quality = quality_scan(Path(job.output_dir)).summary()
            except Exception:
                job.quality = ""
            if job.status == "error":
                job.message = tr("Bazı bloklar hata verdi; 'Kaldığı yerden devam et' ile eksikler tamamlanabilir.")
            self.history.update(job)
            self._notify(tr("{name} hazır", name=job.display_name),
                        tr("{sure} sürdü · {kalite}", sure=format_duration(job.duration_sec), kalite=(job.quality or tr("kalite taraması yapıldı"))))
        if b:
            b.status = "bitti" if (job and job.status == "done") else "hata"; self.queue.save(); self.home.refresh_book(b)
            self._batch_done.append(b.id)
        self._batch_index += 1
        self._run_next()

    def _finish_batch(self) -> None:
        last = None
        for bid in reversed(self._batch_done):
            b = self.queue.get(bid)
            if b and b.job_id and self.history.get(b.job_id):
                last = self.history.get(b.job_id); break
        self.queue.clear_finished()
        if last:
            self.done.show_job(last, others_done=len(self._batch_done) - 1)
            self.stack.setCurrentWidget(self.done)
            if len(self._batch_done) > 1:
                self._notify(tr("Tüm kitaplar bitti"), tr("{n} kitap dönüştürüldü.", n=len(self._batch_done)))
        else:
            self.go_home()
        self._book = None; self._job = None

    def _on_book_failed(self, msg: str) -> None:
        self._end_run()
        if self._job:
            self._job.status = "paused" if self._job.done_blocks else "error"; self._job.message = msg
            self._job.duration_sec = self._duration_base + int(time.monotonic() - self._job_started); self.history.update(self._job)
        if self._book:
            self._book.status = "hata"; self._book.message = msg; self.queue.save(); self.home.refresh_book(self._book)
        QMessageBox.critical(self, APP_NAME, tr("Dönüştürme durdu:\n{msg}", msg=msg))
        self._batch_index += 1
        self._run_next()

    def _on_stopped(self) -> None:
        self._end_run()
        if self._job:
            self._job.status = "paused"; self._job.message = tr("Kullanıcı durdurdu.")
            self._job.duration_sec = self._duration_base + int(time.monotonic() - self._job_started); self.history.update(self._job)
        if self._book:
            if getattr(self, "_skipping", False):
                self._book.status = "atlandi"
            else:
                self._book.status = "test-tamam" if self._book.test else "bekliyor"
            self.queue.save(); self.home.refresh_book(self._book)
        if getattr(self, "_skipping", False):
            self._skipping = False; self._batch_index += 1; self._run_next(); return
        self._book = None; self._job = None
        self.go_home()

    def on_stop(self) -> None:
        self.convert.set_stopping()
        if self._runner and self._runner.is_running():
            self._runner.stop()
        else:
            self._on_stopped()

    def on_skip(self) -> None:
        self._skipping = True
        self.on_stop()

    def on_open_log(self, job_id: str) -> None:
        job = self.history.get(job_id)
        if job and job.log_path and Path(job.log_path).exists():
            open_in_explorer(Path(job.log_path).parent)
        else:
            QMessageBox.information(self, APP_NAME, tr("Bu iş için henüz günlük dosyası yok."))

    # ====================== ayarlar ======================
    def on_clean_raw(self) -> None:
        dirs = find_raw_dirs([Path(j.output_dir) for j in self.history.completed()])
        freed = clean_raw_dirs(dirs)
        self.settings_page.show_clean_result(freed)
        self.settings_page.set_clean_info(0, 0)

    # ====================== bildirim ======================
    def _notify(self, title: str, text: str) -> None:
        if self.settings.notifications and self.tray.isVisible():
            self.tray.showMessage(title, text, QSystemTrayIcon.Information, 8000)

    def closeEvent(self, event) -> None:
        if self._runner and self._runner.is_running():
            ans = QMessageBox.question(self, APP_NAME, tr("Dönüştürme sürüyor. Kapatırsan biten bloklar saklanır ve sonra devam edebilirsin.\nKapatılsın mı?"))
            if ans != QMessageBox.Yes:
                event.ignore(); return
            self._runner.stop()
            if self._job:
                self._job.status = "paused"; self._job.message = tr("Program kapatıldı."); self.history.update(self._job)
            if self._book:
                self._book.status = "test-tamam" if self._book.test else "bekliyor"; self.queue.save()
        if self._installer and self._installer.isRunning():
            self._installer.cancel.set()
        keep_awake(False)
        event.accept()
