import re
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF

from .utils import (
    TITLE_CLEANUP_REGEX,
    MAX_TITLE_LENGTH,
    Chapter,
    Config,
    is_chapter_title
)


def find_chapters_by_style(doc: fitz.Document, config: Config) -> List[Chapter]:
    """Finds chapter start pages by analyzing text style and content."""
    found_chapters = []

    regex_pattern = config.chapter_regex
    try:
        pattern = re.compile(regex_pattern, re.IGNORECASE)
        print(f"\nUsing pattern to find chapters: '{regex_pattern}'")
    except re.error as e:
        print(f"Error: Invalid CHAPTER_REGEX in config file. Reason: {e}")
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
                            found_chapters.append(
                                Chapter(title=text, page=page_num + 1)
                            )
    return found_chapters


def merge_chapters(doc: fitz.Document, chapters: List[Chapter], out_path: Path):
    """Merges selected chapters into a single PDF file."""
    print(f"\nMerging {len(chapters)} sections into one file...")
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
    if not chapters:
        print("\nWarning: No chapters were provided or found to split.")
        return

    out_dir.mkdir(parents=True, exist_ok=True)
    
    # Ensure unique pages and sorted
    chapters.sort(key=lambda x: x.page)
    unique_chapters = []
    seen_pages = set()
    for ch in chapters:
        if ch.page not in seen_pages:
            unique_chapters.append(ch)
            seen_pages.add(ch.page)
    chapters = unique_chapters

    print(f"\nFound {len(chapters)} sections. Splitting document...")
    for i, chapter in enumerate(chapters):
        start_page = chapter.page - 1
        end_page = doc.page_count - 1
        if i + 1 < len(chapters):
            end_page = chapters[i + 1].page - 2

        if start_page > end_page:
            print(f"Warning: Skipping '{chapter.title}' due to invalid page range.")
            continue

        # Sanitize title
        clean_title = re.sub(TITLE_CLEANUP_REGEX, "", chapter.title).strip()
        clean_title = clean_title.replace(' ', '_')[:MAX_TITLE_LENGTH]
        if not clean_title:
            clean_title = f"Section_{i+1}"
            
        out_path = out_dir / f"{i + 1:02d}_{clean_title}.pdf"

        with fitz.open() as writer:
            writer.insert_pdf(doc, from_page=start_page, to_page=end_page)
            writer.save(out_path)
        print(f"  - Created '{out_path}' (Pages {start_page + 1}-{end_page + 1})")


def process_pdf_automatic(doc: fitz.Document, config_path: Path) -> List[Chapter]:
    """Orchestrates the automatic PDF splitting process."""
    chapters = []
    config = Config.from_file(config_path)

    toc = doc.get_toc()
    if toc:
        print("\nFound bookmarks. Splitting by all top-level (Level 1) entries.")
        chapters = [
            Chapter(title=item[1], page=item[2])
            for item in toc
            if item[0] == 1
        ]

    if not chapters:
        print("\nNo top-level bookmarks found. Analyzing text styles as a fallback.")
        is_text_based = any(page.get_text("text") for page in doc)
        if not is_text_based:
            print("\nERROR: This PDF appears to be image-based (scanned).")
            print("Automatic mode cannot process it. Please use Manual Mode.")
            return []
        chapters = find_chapters_by_style(doc, config)

    return chapters


def process_pdf_manual(pages_str: str) -> Optional[List[Chapter]]:
    """Processes a user-provided string of page numbers."""
    if not pages_str:
        return []
    try:
        pages = sorted(list(set([int(p.strip()) for p in pages_str.split(',')])))
        if len(pages) == 1 and pages[0] > 1:
            pages.insert(0, 1)
        return [Chapter(title=f'Section_Page_{p}', page=p) for p in pages]
    except ValueError:
        print("Error: Invalid page numbers provided. Please use comma-separated integers.")
        return None
