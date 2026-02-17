# PDFPy Documentation

PDFPy is a command-line utility designed to split PDF documents into chapters or sections based on bookmarks, text styles, or manual page ranges.

## 1. Core Architecture

The system is modularized for clarity and testability:
- `pdfpy/cli.py`: Command-line interface and argument parsing.
- `pdfpy/core.py`: Core logic for PDF processing and splitting.
- `pdfpy/utils.py`: Shared utilities, constants, and data structures.
- `pdfpy/__main__.py`: Entry point for package-level execution.

### 1.1. Key Classes and Data Structures

- **`Chapter` (Dataclass)**: Represents a detected or specified section with a title and a starting page number (1-indexed).
- **`Config` (Dataclass)**: Manages style-based detection parameters.
  - `chapter_regex`: Regex pattern to match chapter titles.
  - `min_font_size`: Minimum font size threshold.
  - `must_be_bold`: Boolean flag for font weight requirement.

## 2. Execution

The application can be executed as a module:
```bash
python -m pdfpy [pdf_file] [options]
```

## 3. Modes of Operation

### 3.1. Automatic Mode
1.  **Bookmark Detection**: Attempts to retrieve Level 1 bookmarks (TOC).
2.  **Style Fallback**: If no bookmarks are found, scans every page for text matching the `Config` criteria.
3.  **Conflict Resolution**: Ensures unique pages and sorts chapters chronologically.

### 3.2. Manual Mode
- Accepts a comma-separated list of page numbers via the `--manual` flag.
- **Smart Split**: If a single page number $N > 1$ is provided, the system automatically treats it as a split into $[1, N]$, creating two sections.

## 4. Features

### 4.1. Merged Output (`--merge`)
Instead of creating multiple files, the system can consolidate all selected chapters into a single output PDF, preserving only the relevant pages.

### 4.2. Versioning (`--version`)
Standard version tracking for CLI utility maintenance.

## 5. Quality Assurance

### 5.1. Test Suite
Located in `__tests__/`, the suite uses `pytest` and covers:
- **Config Parsing**: Validates default values and file loading.
- **Manual Processing**: Ensures correct transformation of user input.
- **Chapter Detection**: Verifies style-based matching logic.
- **Split Logic**: Confirms correct page range extraction and file creation.
- **Execution**: Verifies package-level module execution.

### 5.2. Error Handling
- Robust against missing configuration files (uses defaults).
- Sanitizes file titles to prevent OS-level path errors.
- Gracefully handles corrupt or invalid PDF files.

## 6. Development Standards
- **SOLID Principles**: Focused functions (SRP), clear data structures.
- **TDD Workflow**: Features are verified against an automated test suite.
- **Documentation**: Handcrafted external Markdown files for clarity.
