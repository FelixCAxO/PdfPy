# PDFPy Documentation

## 1. Sprint Outcome (TDD)

This sprint followed strict TDD:
1. Expanded edge-case and scale coverage first in `__tests__/`.
2. Ran tests in red phase to expose real failures.
3. Refactored implementation to fix root causes (no feature removals).
4. Re-ran full suite to green.

Current test result: `34 passed`.

## 2. Architecture

Main modules:
- `pdfpy/cli.py`: CLI entrypoint and user flow.
- `pdfpy/core.py`: PDF processing orchestration and split/merge logic.
- `pdfpy/utils.py`: shared data classes, constants, and detection helpers.
- `pdfpy/__main__.py`: `python -m pdfpy` package execution.

Core data structures:
- `Chapter(title: str, page: int)`
- `Config(chapter_regex, min_font_size, must_be_bold, ocr_regexes, ocr_fallback_to_first_page, ocr_render_dpi)`

## 3. Behavior Contracts

### 3.1 Automatic mode (`process_pdf_automatic`)

- Uses Level 1 bookmarks first when available.
- If no Level 1 bookmark chapters are available, falls back to style-based text detection.
- For image/scanned PDFs with no extractable text:
  - when `allow_ocr=False`: returns `[]` and reports OCR/manual guidance.
  - when `allow_ocr=True`: attempts OCR extraction using configurable OCR regexes.

### 3.2 OCR fallback for scanned PDFs (`find_chapters_by_ocr`)

- Uses real OCR (no mocking) via runtime dependencies:
  - `pytesseract`
  - `Pillow`
  - local Tesseract OCR binary
- Tries standard Tesseract install paths automatically when PATH is missing.
- Renders each page at configured DPI (`OCR_RENDER_DPI`) and OCRs grayscale images.
- Matches OCR lines against dynamic regex set:
  - `CHAPTER_REGEX`
  - `OCR_REGEXES` list from config
- If no OCR regex matches and `OCR_FALLBACK_TO_FIRST_PAGE=true`, it returns a single section at page 1 so scanned PDFs still split.

CLI support:
- `python -m pdfpy your.pdf --ocr`

### 3.3 Configurable OCR keys (`pdfpy/chapters_config.md`)

- `OCR_REGEXES`: `||`-separated regex list for OCR matching.
- `OCR_FALLBACK_TO_FIRST_PAGE`: when true, scanned PDFs with no regex match still produce one split from page 1.
- `OCR_RENDER_DPI`: OCR render DPI (higher can improve OCR accuracy but costs more time).

### 3.4 Style abstraction (`find_chapters_by_style`)

- Regex compilation is case-insensitive.
- Chapter detection uses style constraints from `Config`:
  - minimum font size
  - optional bold requirement
  - regex match on span text
- Only one chapter is captured per page (first valid match).
- Invalid regex in config is handled safely by returning `[]`.

### 3.5 Manual mode (`process_pdf_manual`)

- Input `None`, empty string, whitespace-only, or comma-only resolves to `[]`.
- Empty comma tokens are ignored (`"1,,3"` => pages 1 and 3).
- Any non-integer token or non-positive page (`<= 0`) is invalid and returns `None`.
- Valid pages are de-duplicated and sorted.
- Single page `N > 1` auto-expands to `[1, N]`.

### 3.6 Split and merge normalization

Split and merge share normalization semantics:
- Sort chapters by page.
- Remove duplicate chapter pages.
- Ignore out-of-range pages (`< 1` or `> doc.page_count`).

#### Split (`perform_split`)
- Creates one PDF per normalized chapter range.
- Skips invalid computed ranges safely.
- Sanitizes file names by removing forbidden path characters.
- Uses fallback file names (`Section_X`) when sanitized titles become empty.
- Truncates titles to `MAX_TITLE_LENGTH`.

#### Merge (`merge_chapters`)
- Merges normalized chapter ranges in order.
- Ignores invalid/out-of-range chapters safely.

## 4. Test Coverage

Test suite location: `__tests__/`

Key coverage includes:
- Config defaults, partial files, and loading behavior.
- CLI/module execution.
- Manual parsing edge cases (whitespace, empty tokens, invalid tokens, non-positive pages, dedupe/sort).
- Style detection across text variants (case-insensitive matches, custom Roman numeral regex, invalid regex handling).
- Automatic flow decisions (TOC Level 1 priority, fallback behavior, non-text PDF handling).
- Scanned PDF OCR behavior (OCR detection, OCR no-match dynamic first-page fallback, OCR disabled behavior).
- Split/merge boundary handling (invalid pages, duplicates, sanitized/truncated titles, ordered merge output).
- Scale tests with large documents and many sections for split/merge/detection stability.

## 5. Real PDF Validation

Online integration sweeps were executed against text, mixed, and scanned PDFs.
Observed result: scanned one-page files (`ccitt`, `skew`, `jbig2`) now produce merged output in OCR mode via dynamic first-page fallback.

## 6. Quality Notes

- Fixes are non-destructive and root-cause oriented.
- OCR extraction is now config-driven and dynamic rather than single-regex only.
- Public behavior is more predictable across manual, split, merge, and scanned-PDF OCR paths.
