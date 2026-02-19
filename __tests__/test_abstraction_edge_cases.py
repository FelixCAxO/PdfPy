from pathlib import Path

import fitz

from pdfpy import (
    Chapter,
    Config,
    find_chapters_by_style,
    merge_chapters,
    perform_split,
    process_pdf_automatic,
)


class _DocWithForcedToc:
    def __init__(self, doc, toc):
        self._doc = doc
        self._toc = toc

    def get_toc(self):
        return self._toc

    def __iter__(self):
        return iter(self._doc)


def _create_numbered_pdf(pdf_path: Path, page_count: int) -> None:
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page()
        page.insert_text((50, 50), f"Page {i + 1}")
    doc.save(pdf_path)
    doc.close()


def test_find_chapters_by_style_is_case_insensitive(tmp_path):
    pdf_path = tmp_path / "case_insensitive.pdf"
    doc = fitz.open()

    page = doc.new_page()
    page.insert_text((50, 50), "CHAPTER 1: INTRO", fontsize=20, fontname="helv")

    page = doc.new_page()
    page.insert_text((50, 50), "chapter 2: Methods", fontsize=20, fontname="helv")

    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    config = Config(min_font_size=18, must_be_bold=False)
    chapters = find_chapters_by_style(doc, config)
    doc.close()

    assert [(chapter.title, chapter.page) for chapter in chapters] == [
        ("CHAPTER 1: INTRO", 1),
        ("chapter 2: Methods", 2),
    ]


def test_find_chapters_by_style_supports_custom_regex_for_roman_numerals(tmp_path):
    pdf_path = tmp_path / "roman_parts.pdf"
    doc = fitz.open()

    page = doc.new_page()
    page.insert_text((50, 50), "Part I - Getting Started", fontsize=22, fontname="helv")

    page = doc.new_page()
    page.insert_text((50, 50), "Part II - Advanced", fontsize=22, fontname="helv")

    page = doc.new_page()
    page.insert_text((50, 50), "Body text", fontsize=12, fontname="helv")

    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    config = Config(
        chapter_regex=r"^Part\s+[IVXLC]+",
        min_font_size=20,
        must_be_bold=False,
    )
    chapters = find_chapters_by_style(doc, config)
    doc.close()

    assert [(chapter.title, chapter.page) for chapter in chapters] == [
        ("Part I - Getting Started", 1),
        ("Part II - Advanced", 2),
    ]


def test_find_chapters_by_style_keeps_first_match_per_page(tmp_path):
    pdf_path = tmp_path / "multiple_matches_same_page.pdf"
    doc = fitz.open()

    page = doc.new_page()
    page.insert_text((50, 50), "Chapter 1: Alpha", fontsize=20, fontname="helv")
    page.insert_text((50, 80), "Chapter 2: Beta", fontsize=20, fontname="helv")

    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    config = Config(min_font_size=18, must_be_bold=False)
    chapters = find_chapters_by_style(doc, config)
    doc.close()

    assert len(chapters) == 1
    assert chapters[0].title == "Chapter 1: Alpha"
    assert chapters[0].page == 1


def test_find_chapters_by_style_returns_empty_for_invalid_regex(tmp_path):
    pdf_path = tmp_path / "invalid_regex.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Chapter 1: Introduction", fontsize=20, fontname="helv")
    doc.save(pdf_path)
    doc.close()

    doc = fitz.open(pdf_path)
    config = Config(chapter_regex=r"(", min_font_size=18, must_be_bold=False)
    chapters = find_chapters_by_style(doc, config)
    doc.close()

    assert chapters == []


def test_process_pdf_automatic_prefers_level_one_bookmarks(tmp_path):
    doc = fitz.open()
    for _ in range(3):
        doc.new_page()

    doc.set_toc([
        [1, "Preface", 1],
        [2, "Nested section", 2],
        [1, "Appendix", 3],
    ])

    chapters = process_pdf_automatic(doc, tmp_path / "missing_config.md")
    doc.close()

    assert [(chapter.title, chapter.page) for chapter in chapters] == [
        ("Preface", 1),
        ("Appendix", 3),
    ]


def test_process_pdf_automatic_falls_back_when_toc_has_no_level_one(tmp_path):
    config_path = tmp_path / "chapters_config.md"
    config_path.write_text(
        "CHAPTER_REGEX: ^Chapter\\s+\\d+\nMIN_FONT_SIZE: 18\nMUST_BE_BOLD: false\n",
        encoding="utf-8",
    )

    base_doc = fitz.open()
    page = base_doc.new_page()
    page.insert_text((50, 50), "Chapter 1: Introduction", fontsize=20, fontname="helv")
    base_doc.new_page()

    wrapped_doc = _DocWithForcedToc(base_doc, [[2, "Nested only", 1]])

    chapters = process_pdf_automatic(wrapped_doc, config_path)
    base_doc.close()

    assert [(chapter.title, chapter.page) for chapter in chapters] == [
        ("Chapter 1: Introduction", 1),
    ]


def test_process_pdf_automatic_returns_empty_for_non_text_pdf(tmp_path):
    doc = fitz.open()
    doc.new_page()
    doc.new_page()

    chapters = process_pdf_automatic(doc, tmp_path / "missing_config.md")
    doc.close()

    assert chapters == []


def test_perform_split_ignores_invalid_pages_and_duplicates(tmp_path):
    pdf_path = tmp_path / "numbered.pdf"
    _create_numbered_pdf(pdf_path, page_count=6)

    doc = fitz.open(pdf_path)
    out_dir = tmp_path / "split_output"
    chapters = [
        Chapter(title="Zero", page=0),
        Chapter(title="Two", page=2),
        Chapter(title="Duplicate Two", page=2),
        Chapter(title="Five", page=5),
        Chapter(title="Too Large", page=99),
    ]
    perform_split(doc, chapters, out_dir)
    doc.close()

    output_files = sorted(path.name for path in out_dir.glob("*.pdf"))
    assert output_files == ["01_Two.pdf", "02_Five.pdf"]

    first = fitz.open(out_dir / "01_Two.pdf")
    assert first.page_count == 3
    first.close()

    second = fitz.open(out_dir / "02_Five.pdf")
    assert second.page_count == 2
    second.close()


def test_perform_split_sanitizes_titles_and_uses_fallback_name(tmp_path):
    pdf_path = tmp_path / "sanitize_titles.pdf"
    _create_numbered_pdf(pdf_path, page_count=2)

    doc = fitz.open(pdf_path)
    out_dir = tmp_path / "sanitized_output"
    chapters = [
        Chapter(title='\\/*?:"><|', page=1),
        Chapter(title="A" * 130, page=2),
    ]
    perform_split(doc, chapters, out_dir)
    doc.close()

    assert (out_dir / "01_Section_1.pdf").exists()
    assert (out_dir / f"02_{'A' * 100}.pdf").exists()


def test_merge_chapters_sorts_and_ignores_invalid_pages(tmp_path):
    pdf_path = tmp_path / "merge_numbered.pdf"
    _create_numbered_pdf(pdf_path, page_count=8)

    doc = fitz.open(pdf_path)
    out_path = tmp_path / "merged_sorted.pdf"
    chapters = [
        Chapter(title="Late", page=8),
        Chapter(title="Invalid low", page=0),
        Chapter(title="Middle", page=3),
        Chapter(title="Invalid high", page=99),
    ]
    merge_chapters(doc, chapters, out_path)
    doc.close()

    assert out_path.exists()
    merged = fitz.open(out_path)
    assert merged.page_count == 6
    assert "Page 3" in merged[0].get_text("text")
    merged.close()
