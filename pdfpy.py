"""
A command-line utility to split a PDF file into separate chapters.

This script offers two primary modes of operation:
1.  Automatic Mode: Detects chapters using bookmarks or text style analysis.
2.  Manual Mode: Splits the PDF based on a user-provided list of page numbers.

Usage:
    Automatic: python pdfpy.py path/to/your/document.pdf
    Manual:    python pdfpy.py path/to/your/document.pdf --manual "5,10,56"

Limitation: The automatic mode cannot process image-based (scanned) PDFs.
"""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import fitz  # PyMuPDF

VERSION = "2.0.0"
CONFIG_FILE_NAME = "chapters_config.md"
MAX_TITLE_LENGTH = 100
TITLE_CLEANUP_REGEX = r'[\\/*?:"<>|]'


@dataclass
class Chapter:
    """Represents a single chapter with a title and starting page."""
    title: str
    page: int


@dataclass
class Config:
    """Configuration for style-based chapter detection."""
    chapter_regex: str = r'^Chapter\s+\d+'
    min_font_size: float = 16.0
    must_be_bold: bool = True

    @staticmethod
    def from_file(config_path: Path) -> 'Config':
        """Parses the chapter style configuration file."""
        config = Config()
        if not config_path.is_file():
            print(f"Info: Configuration file not found at '{config_path}'. Using defaults.")
            return config

        try:
            with config_path.open('r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line and not line.strip().startswith('<!--'):
                        key, value = map(str.strip, line.split(':', 1))
                        if key == 'CHAPTER_REGEX':
                            config.chapter_regex = value
                        elif key == 'MIN_FONT_SIZE':
                            try:
                                config.min_font_size = float(value)
                            except ValueError:
                                pass
                        elif key == 'MUST_BE_BOLD':
                            config.must_be_bold = value.lower() == 'true'
        except Exception as e:
            print(f"Warning: Could not parse configuration file. Error: {e}")
        
        return config


def _is_chapter_title(text: str, span: dict, pattern: re.Pattern, config: Config) -> bool:
    """Checks if a text span matches the chapter title criteria."""
    is_large_enough = span["size"] >= config.min_font_size
    is_bold = "bold" in span["font"].lower()
    bold_ok = not config.must_be_bold or is_bold
    matches_pattern = pattern.match(text)
    return is_large_enough and bold_ok and bool(matches_pattern)


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
                    if _is_chapter_title(text, span, pattern, config):
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


def main() -> None:
    """Entry point for the command-line application."""
    parser = argparse.ArgumentParser(description="Split a PDF document into chapters.")
    parser.add_argument("pdf_file", type=Path, nargs='?', help="Path to the source PDF file.")
    parser.add_argument(
        "--manual",
        metavar="PAGES",
        type=str,
        help="Provide a comma-separated list of starting page numbers.",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge the found sections into a single PDF instead of splitting.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show the version of the script and exit."
    )
    args = parser.parse_args()

    if not args.pdf_file:
        parser.print_help()
        return

    pdf_path: Path = args.pdf_file

    if not pdf_path.is_file() or pdf_path.suffix.lower() != '.pdf':
        print(f"Error: Path '{pdf_path}' is not a valid PDF file.")
        return

    script_dir = Path(__file__).parent.resolve()
    config_file = script_dir / CONFIG_FILE_NAME
    
    # Handle output path
    if args.merge:
        output_dest = pdf_path.parent / f"{pdf_path.stem}_merged.pdf"
    else:
        output_dest = pdf_path.parent / f"{pdf_path.stem}_chapters"

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error: Could not read '{pdf_path}'. Reason: {e}")
        return

    chapters_to_split = []
    if args.manual is not None:
        print("Running in Manual Mode...")
        chapters_to_split = process_pdf_manual(args.manual)
    else:
        print("Running in Automatic Mode...")
        chapters_to_split = process_pdf_automatic(doc, config_file)

    if chapters_to_split:
        if args.merge:
            merge_chapters(doc, chapters_to_split, output_dest)
        else:
            perform_split(doc, chapters_to_split, output_dest)
    else:
        print("No valid chapters found or an error occurred.")

    doc.close()
    print("\nProcessing complete.")


if __name__ == '__main__':
    main()