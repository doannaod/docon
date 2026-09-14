"""Arayüzü kilitlemeyen arka plan işleri (QThread)."""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from app.core.analyzer import PdfAnalysis, analyze_pdf
from app.core.environment import EnvironmentStatus, check_environment
from app.core.update_check import check_for_update


class AnalyzeWorker(QThread):
    finished_with = Signal(object)  # PdfAnalysis

    def __init__(self, pdf_path: str, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path

    def run(self) -> None:
        result: PdfAnalysis = analyze_pdf(self.pdf_path)
        self.finished_with.emit(result)


class EnvironmentCheckWorker(QThread):
    finished_with = Signal(object)  # EnvironmentStatus

    def run(self) -> None:
        status: EnvironmentStatus = check_environment(deep=True)
        self.finished_with.emit(status)


class UpdateCheckWorker(QThread):
    finished_with = Signal(object)  # str | None (yeni sürüm tag'i, yoksa None)

    def __init__(self, current_version: str, parent=None):
        super().__init__(parent)
        self.current_version = current_version

    def run(self) -> None:
        tag = check_for_update(self.current_version)
        self.finished_with.emit(tag)
