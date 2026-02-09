# PdfPy

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-2.0.0-green.svg)](#)

PdfPy is a Python utility that splits PDF documents into chapters using bookmark hierarchy, style-based detection, or manual page selection.

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Split a PDF automatically
python -m pdfpy path/to/document.pdf

# Split at specific pages manually
python -m pdfpy path/to/document.pdf --manual "5,10,15"
```

---

## Features

- **Smart Detection**: Automatically identifies chapters using PDF bookmarks (TOC).
- **Style Fallback**: If bookmarks are missing, it uses font size and regex patterns to find chapter titles.
- **Configurable**: Fine-tune detection rules in `pdfpy/chapters_config.md` without touching the code.
- **Manual Mode**: Explicitly define split points for precise control.
- **Merge Option**: Consolidate detected sections into a single clean PDF.
- **Drag & Drop**: Windows-ready batch files for zero-command usage.

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/FelixCAxO/Pdfpy.git
   cd Pdfpy
   ```

2. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### Command Line Interface

PdfPy is structured as a package. Run it using:

```bash
# Automatic mode (bookmarks -> style fallback)
python -m pdfpy path/to/your/document.pdf

# Manual mode (comma-separated start pages)
python -m pdfpy path/to/your/document.pdf --manual "5,12,45"

# Merging sections instead of splitting
python -m pdfpy path/to/your/document.pdf --merge
```

### Windows Drag-and-Drop

- **`run_auto.bat`**: Drag a PDF here to split it automatically.
- **`run_manual.bat`**: Drag a PDF here to be prompted for manual split pages.

### Mac & Linux (Terminal)

- **`run_auto.sh`**: `./run_auto.sh path/to/document.pdf`
- **`run_manual.sh`**: `./run_manual.sh path/to/document.pdf`

---

## Configuration

Heuristic detection settings are managed in `pdfpy/chapters_config.md`:

- `CHAPTER_REGEX`: Regex pattern for titles (e.g., `^Chapter \d+`).
- `MIN_FONT_SIZE`: Minimum font size to consider as a title.
- `MUST_BE_BOLD`: Require bold font for titles (`true`/`false`).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
