# PdfPy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](#)

PdfPy is a Python utility that splits PDF documents into chapters using bookmark hierarchy, style-based detection, OCR fallback (for scanned PDFs), or manual page selection.

---

## Quick Start

```bash
# Install as editable package
pip install -e .

# Split a PDF automatically
pdfpy path/to/document.pdf

# Or using the scripts
./scripts/run_auto.sh path/to/document.pdf
```

---

## Features

- **Smart Detection**: Automatically identifies chapters using PDF bookmarks (TOC).
- **Style Fallback**: If bookmarks are missing, it uses font size and regex patterns to find chapter titles.
- **OCR Fallback**: Optional OCR path for scanned/image-based PDFs (`--ocr`).
- **Dynamic OCR Extraction**: Configurable OCR regex list plus first-page fallback mode for scans without clear chapter headings.
- **Configurable**: Fine-tune detection rules in `src/pdfpy/chapters_config.md` without touching the code.
- **Manual Mode**: Explicitly define split points for precise control.
- **Merge Option**: Consolidate detected sections into a single clean PDF.
- **Drag & Drop**: Windows-ready batch files in `scripts/` for zero-command usage.

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/FelixCAxO/Pdfpy.git
   cd Pdfpy
   ```

2. **Install as editable package**:
   ```bash
   pip install -e .
   ```

3. **Optional OCR setup (for scanned PDFs)**:
   ```bash
   pip install -e ".[ocr]"
   ```
   Also install the local Tesseract OCR binary and ensure it is available on your system PATH.

---

## Usage

### Command Line Interface

If installed as a package, use the `pdfpy` command:

```bash
# Automatic mode (bookmarks -> style fallback)
pdfpy path/to/your/document.pdf

# Automatic mode + OCR fallback for scanned/image PDFs
pdfpy path/to/your/document.pdf --ocr

# Manual mode (comma-separated start pages)
pdfpy path/to/your/document.pdf --manual "5,12,45"
```

### Windows Drag-and-Drop (in `scripts/`)

- **`scripts/run_auto.bat`**: Drag a PDF here to split it automatically.
- **`scripts/run_manual.bat`**: Drag a PDF here to be prompted for manual split pages.

### Mac & Linux (in `scripts/`)

- **`scripts/run_auto.sh`**: `./scripts/run_auto.sh path/to/document.pdf`
- **`scripts/run_manual.sh`**: `./scripts/run_manual.sh path/to/document.pdf`

---

## Configuration

Heuristic detection settings are managed in `src/pdfpy/chapters_config.md`:

- `CHAPTER_REGEX`: Regex pattern for style-based title detection (e.g., `^Chapter \d+`).
- `MIN_FONT_SIZE`: Minimum font size to consider as a style title.
- `MUST_BE_BOLD`: Require bold font for style-based title detection (`true`/`false`).
- `OCR_REGEXES`: OCR regex list separated by `||` (used in scanned PDF mode).
- `OCR_FALLBACK_TO_FIRST_PAGE`: If OCR finds no chapter regex match, still split from page 1 (`true`/`false`).
- `OCR_RENDER_DPI`: OCR rendering DPI (e.g., `300`, `400`, `600`).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
