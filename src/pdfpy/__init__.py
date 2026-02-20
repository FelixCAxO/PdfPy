from .utils import VERSION, Chapter, Config, is_chapter_title
from .core import (
    find_chapters_by_style,
    merge_chapters,
    perform_split,
    process_pdf_automatic,
    process_pdf_manual,
)
from .cli import main

__version__ = VERSION
__all__ = [
    "VERSION",
    "Chapter",
    "Config",
    "is_chapter_title",
    "find_chapters_by_style",
    "merge_chapters",
    "perform_split",
    "process_pdf_automatic",
    "process_pdf_manual",
    "main",
]
