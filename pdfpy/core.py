import re
from io import BytesIO
from pathlib import Path
from typing import List, Optional, Pattern, Tuple

import fitz  # PyMuPDF

from .utils import (
    TITLE_CLEANUP_REGEX,
    MAX_TITLE_LENGTH,
    Chapter,
    Config,
    is_chapter_title,
)


def _normalize_chapters(chapters: List[Chapter], page_count: int) -> List[Chapter]:
    """Sorts chapters and removes duplicates / out-of-range pages."""
    if page_count <= 0:
        return []

    normalized: List[Chapter] = []
    seen_pages = set()

    for chapter in sorted(chapters, key=lambda item: item.page):
        if chapter.page in seen_pages:
            continue

        if not (1 <= chapter.page <= page_count):
            print(
                f"Warning: Ignoring '{chapter.title}' because page {chapter.page} "
                f"is outside valid range 1-{page_count}."
            )
            continue

        normalized.append(chapter)
        seen_pages.add(chapter.page)

    return normalized


def _parse_manual_pages(pages_str: Optional[str]) -> Optional[List[int]]:
    """Parses manual page input into a validated, sorted, unique list."""
    if pages_str is None:
        return []

    if not pages_str.strip():
        return []

    tokens = [token.strip() for token in pages_str.split(",") if token.strip()]
    if not tokens:
        return []

    pages: List[int] = []
    for token in tokens:
        try:
            page = int(token)
        except ValueError:
            return None

        if page <= 0:
            return None

        pages.append(page)

    unique_pages = sorted(set(pages))
    if len(unique_pages) == 1 and unique_pages[0] > 1:
        unique_pages.insert(0, 1)

    return unique_pages


def _compile_chapter_pattern(config: Config) -> Optional[Pattern[str]]:
    """Compiles chapter regex once and handles malformed patterns safely."""
    regex_pattern = config.chapter_regex
    try:
        pattern = re.compile(regex_pattern, re.IGNORECASE)
        print(f"\nUsing pattern to find chapters: '{regex_pattern}'")
        return pattern
    except re.error as error:
        print(f"Error: Invalid CHAPTER_REGEX in config file. Reason: {error}")
        return None


def _compile_ocr_patterns(config: Config) -> List[Pattern[str]]:
    """Compiles OCR regex patterns from config and skips invalid entries."""
    compiled: List[Pattern[str]] = []
    seen = set()

    raw_patterns = [config.chapter_regex] + list(config.ocr_regexes)
    for regex_pattern in raw_patterns:
        candidate = regex_pattern.strip()
        if not candidate or candidate in seen:
            continue

        seen.add(candidate)
        try:
            compiled.append(re.compile(candidate, re.IGNORECASE))
        except re.error as error:
            print(f"Warning: Ignoring invalid OCR regex '{candidate}'. Reason: {error}")

    if compiled:
        preview = ", ".join(pattern.pattern for pattern in compiled)
        print(f"\nUsing OCR patterns: {preview}")
    else:
        print("Warning: No valid OCR regex patterns available.")

    return compiled


def _normalize_ocr_line(line: str) -> str:
    """Normalizes OCR output line for matching."""
    candidate = re.sub(r"\s+", " ", line).strip()
    candidate = re.sub(r"^[^\w]+", "", candidate)
    return candidate


def _load_ocr_dependencies() -> Tuple[Optional[object], Optional[object]]:
    """Loads optional OCR dependencies at runtime."""
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        return None, None

    try:
        _ = pytesseract.get_tesseract_version()
        return pytesseract, Image
    except Exception:
        candidate_paths = [
            Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
            Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        ]

        for candidate in candidate_paths:
            if not candidate.is_file():
                continue

            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            try:
                _ = pytesseract.get_tesseract_version()
                return pytesseract, Image
            except Exception:
                continue

    return None, None


def find_chapters_by_style(doc: fitz.Document, config: Config) -> List[Chapter]:
    """Finds chapter start pages by analyzing text style and content."""
    found_chapters = []
    pattern = _compile_chapter_pattern(config)
    if pattern is None:
        return []

    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if is_chapter_title(text, span, pattern, config):
                        if not any(c.page == page_num + 1 for c in found_chapters):
                            found_chapters.append(Chapter(title=text, page=page_num + 1))
    return found_chapters


def find_chapters_by_ocr(doc: fitz.Document, config: Config) -> List[Chapter]:
    """Finds chapter pages using OCR for scanned/image-based PDFs."""
    found_chapters = []
    patterns = _compile_ocr_patterns(config)

    pytesseract, image_module = _load_ocr_dependencies()
    if pytesseract is None or image_module is None:
        print("OCR dependencies are unavailable. Install pytesseract, Pillow, and Tesseract OCR.")
        return []

    fallback_title = ""

    for page_num, page in enumerate(doc):
        try:
            pixmap = page.get_pixmap(dpi=config.ocr_render_dpi, alpha=False)
            png_bytes = pixmap.tobytes("png")
            with image_module.open(BytesIO(png_bytes)) as image:
                # Grayscale + PSM 6 improves OCR on scanned pages.
                text = pytesseract.image_to_string(image.convert("L"), config="--psm 6")
        except Exception as error:
            print(f"Warning: OCR failed on page {page_num + 1}. Reason: {error}")
            continue

        page_already_captured = any(chapter.page == page_num + 1 for chapter in found_chapters)

        for line in text.splitlines():
            normalized = _normalize_ocr_line(line)
            if not normalized:
                continue

            if not fallback_title:
                fallback_title = normalized[:MAX_TITLE_LENGTH]

            if page_already_captured:
                continue

            if any(pattern.match(normalized) for pattern in patterns):
                found_chapters.append(Chapter(title=normalized, page=page_num + 1))
                page_already_captured = True

    if found_chapters:
        return found_chapters

    if config.ocr_fallback_to_first_page and doc.page_count > 0:
        print("OCR patterns did not match. Falling back to first-page split.")
        title = fallback_title if fallback_title else "Scanned_Section_1"
        return [Chapter(title=title, page=1)]

    return []


def merge_chapters(doc: fitz.Document, chapters: List[Chapter], out_path: Path):
    """Merges selected chapters into a single PDF file."""
    chapters = _normalize_chapters(chapters, doc.page_count)
    print(f"\nMerging {len(chapters)} sections into one file...")

    if not chapters:
        print("Warning: No valid chapters available to merge.")
        return

    with fitz.open() as writer:
        for i, chapter in enumerate(chapters):
            start_page = chapter.page - 1
            end_page = doc.page_count - 1
            if i + 1 < len(chapters):
                end_page = chapters[i + 1].page - 2

            if start_page <= end_page and 0 <= start_page < doc.page_count:
                writer.insert_pdf(doc, from_page=start_page, to_page=end_page)

        writer.save(out_path)
    print(f"  - Created merged document: '{out_path}'")


def perform_split(doc: fitz.Document, chapters: List[Chapter], out_dir: Path):
    """Core logic to split a PDF based on a list of chapters."""
    chapters = _normalize_chapters(chapters, doc.page_count)
    if not chapters:
        print("\nWarning: No chapters were provided or found to split.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nFound {len(chapters)} sections. Splitting document...")
    output_index = 0

    for i, chapter in enumerate(chapters):
        start_page = chapter.page - 1
        end_page = doc.page_count - 1
        if i + 1 < len(chapters):
            end_page = chapters[i + 1].page - 2

        if start_page > end_page:
            print(f"Warning: Skipping '{chapter.title}' due to invalid page range.")
            continue

        output_index += 1

        # Sanitize title
        clean_title = re.sub(TITLE_CLEANUP_REGEX, "", chapter.title).strip()
        clean_title = clean_title.replace(" ", "_")[:MAX_TITLE_LENGTH]
        if not clean_title:
            clean_title = f"Section_{output_index}"

        out_path = out_dir / f"{output_index:02d}_{clean_title}.pdf"

        with fitz.open() as writer:
            writer.insert_pdf(doc, from_page=start_page, to_page=end_page)
            writer.save(out_path)
        print(f"  - Created '{out_path}' (Pages {start_page + 1}-{end_page + 1})")


def process_pdf_automatic(doc: fitz.Document, config_path: Path, allow_ocr: bool = False) -> List[Chapter]:
    """Orchestrates automatic PDF splitting with optional OCR fallback."""
    chapters = []
    config = Config.from_file(config_path)

    toc = doc.get_toc()
    if toc:
        print("\nFound bookmarks. Splitting by all top-level (Level 1) entries.")
        chapters = [Chapter(title=item[1], page=item[2]) for item in toc if item[0] == 1]

    if not chapters:
        print("\nNo top-level bookmarks found. Analyzing text styles as a fallback.")
        is_text_based = any(page.get_text("text") for page in doc)
        if not is_text_based:
            print("\nThis PDF appears to be image-based (scanned).")
            if allow_ocr:
                print("Attempting OCR fallback...")
                chapters = find_chapters_by_ocr(doc, config)
                if chapters:
                    print(f"Found {len(chapters)} sections via OCR.")
                    return chapters
                print("OCR fallback could not detect chapters.")
            else:
                print("OCR fallback is disabled.")

            print("Automatic mode cannot process it reliably. Please use --ocr or Manual Mode.")
            return []

        chapters = find_chapters_by_style(doc, config)

    return chapters


def process_pdf_manual(pages_str: Optional[str]) -> Optional[List[Chapter]]:
    """Processes a user-provided string of page numbers."""
    pages = _parse_manual_pages(pages_str)
    if pages is None:
        print("Error: Invalid page numbers provided. Please use comma-separated positive integers.")
        return None

    return [Chapter(title=f"Section_Page_{page}", page=page) for page in pages]
