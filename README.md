# Docon

**A free Windows desktop app that converts PDF books and technical manuals into a clean,
searchable Markdown library — powered by AI OCR, running entirely on your own computer.**

## Why

Large PDF references — textbooks, engineering manuals, standards, equipment documentation —
are hard to actually use: no real search, tables that fall apart when copied, no easy way to
feed a chapter to an AI assistant, no selectable text at all if the pages are scanned.

Docon converts a PDF like that into a proper Markdown library — real text, tables, and
equations you can search, edit, and reuse — while keeping the original structure and figures
intact.

## What it does

1. Add one or more PDFs to a queue.
2. It runs a quick 50-page test conversion first, so you can check the result before
   committing to the whole book.
3. Converts the full book, split by chapter when a table of contents is available.
4. Produces a Markdown folder per book — text, tables, equations, figures — plus a short
   quality report.

Everything runs locally; no PDF content is uploaded anywhere.

## Under the hood

- **Interface:** PySide6 (Qt) desktop app.
- **OCR engine:** [marker-pdf](https://github.com/datalab-to/marker) with the
  [surya](https://github.com/datalab-to/surya) models, on PyTorch.
- **GPU:** an NVIDIA GPU with CUDA is strongly recommended — conversion is much slower on CPU.
  Docon detects your GPU and warns you before downloading anything if none is found.

## Installation

Docon itself is small; the heavy AI components (a few GB) download automatically on first
launch, with progress and resume support.

1. Download the latest installer from the
   [Releases page](https://github.com/doannaod/docon/releases/latest).
2. Run it — no administrator rights needed.
3. Launch Docon and follow the on-screen first-run setup.

## Language

English, Turkish, and Spanish — switchable from Settings.

## Status

Actively developed and used day-to-day.
