from io import BytesIO
from pathlib import Path

import fitz
import pytest

from pdfpy import (
    Chapter,
    Config,
    find_chapters_by_style,
    merge_chapters,
    perform_split,
    process_pdf_automatic,
)


def _create_text_pdf(pdf_path: Path, page_count: int) -> None:
    doc = fitz.open()
    for i in range(page_count):
        page = doc.new_page()
        page.insert_text((50, 50), f"Page {i + 1}", fontsize=11, fontname="helv")
    doc.save(pdf_path)
    doc.close()


def _create_large_styled_pdf(pdf_path: Path, page_count: int, chapter_every: int) -> None:
    doc = fitz.open()
    chapter_number = 0

    for i in range(page_count):
        page = doc.new_page()
        page_index = i + 1
        if page_index % chapter_every == 1:
            chapter_number += 1
            page.insert_text(
                (50, 50),
                f"Chapter {chapter_number}: Segment {chapter_number}",
                fontsize=20,
                fontname="helv",
            )
        else:
            page.insert_text((50, 50), f"Body page {page_index}", fontsize=11, fontname="helv")

    doc.save(pdf_path)
    doc.close()


def _is_ocr_runtime_available() -> bool:
    try:
        import pytesseract
        from PIL import Image

        _ = Image.new("RGB", (10, 10), "white")
        _ = pytesseract.get_tesseract_version()
        return True
    except Exception:
        try:
            import pytesseract
            from PIL import Image

            for candidate in [
                Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
                Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
            ]:
                if not candidate.is_file():
                    continue
                pytesseract.pytesseract.tesseract_cmd = str(candidate)
                _ = Image.new("RGB", (10, 10), "white")
                _ = pytesseract.get_tesseract_version()
                return True
        except Exception:
            return False

    return False


@pytest.mark.skipif(not _is_ocr_runtime_available(), reason="OCR runtime not available")
def test_process_pdf_automatic_detects_chapter_in_scanned_pdf_with_ocr(tmp_path):
    import pytesseract
    from PIL import Image, ImageDraw

    # Keep imports used so linters do not classify them as unused.
    assert pytesseract is not None

    image = Image.new("RGB", (1800, 2400), "white")
    drawer = ImageDraw.Draw(image)
    drawer.text((140, 180), "Chapter 1: Scan Intro", fill="black")
    drawer.text((140, 260), "This page is an image, not embedded text.", fill="black")

    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    png_bytes = image_bytes.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=png_bytes)

    config_path = tmp_path / "chapters_config.md"
    config_path.write_text("CHAPTER_REGEX: ^Chapter\\s+\\d+\n", encoding="utf-8")

    chapters = process_pdf_automatic(doc, config_path, allow_ocr=True)
    doc.close()

    assert chapters
    assert chapters[0].page == 1


@pytest.mark.skipif(not _is_ocr_runtime_available(), reason="OCR runtime not available")
def test_process_pdf_automatic_scanned_pdf_fallbacks_to_first_page_split_when_no_match(tmp_path):
    from PIL import Image

    image = Image.new("RGB", (1800, 2400), "white")

    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    png_bytes = image_bytes.getvalue()

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, stream=png_bytes)

    config_path = tmp_path / "chapters_config.md"
    config_path.write_text(
        "\n".join(
            [
                "CHAPTER_REGEX: ^NeverWillMatch$",
                "OCR_REGEXES: ^ThisAlsoWillNotMatch$",
                "OCR_FALLBACK_TO_FIRST_PAGE: true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    chapters = process_pdf_automatic(doc, config_path, allow_ocr=True)
    doc.close()

    assert len(chapters) == 1
    assert chapters[0].page == 1


def test_process_pdf_automatic_accepts_ocr_flag_when_disabled(tmp_path):
    doc = fitz.open()
    doc.new_page()

    chapters = process_pdf_automatic(doc, tmp_path / "missing_config.md", allow_ocr=False)
    doc.close()

    assert chapters == []


def test_find_chapters_by_style_large_document(tmp_path):
    pdf_path = tmp_path / "large_styled.pdf"
    _create_large_styled_pdf(pdf_path, page_count=160, chapter_every=8)

    doc = fitz.open(pdf_path)
    config = Config(min_font_size=18, must_be_bold=False)
    chapters = find_chapters_by_style(doc, config)
    doc.close()

    assert len(chapters) == 20
    assert chapters[0].page == 1
    assert chapters[-1].page == 153


def test_perform_split_large_number_of_sections(tmp_path):
    pdf_path = tmp_path / "split_large.pdf"
    _create_text_pdf(pdf_path, page_count=120)

    doc = fitz.open(pdf_path)
    chapters = [Chapter(title=f"Chapter {i}", page=page) for i, page in enumerate(range(1, 121, 3), start=1)]
    out_dir = tmp_path / "split_large_output"

    perform_split(doc, chapters, out_dir)
    doc.close()

    files = sorted(out_dir.glob("*.pdf"))
    assert len(files) == 40

    first = fitz.open(files[0])
    middle = fitz.open(files[19])
    last = fitz.open(files[-1])

    assert first.page_count == 3
    assert middle.page_count == 3
    assert last.page_count == 3

    first.close()
    middle.close()
    last.close()


def test_merge_chapters_large_number_of_sections_with_noise(tmp_path):
    pdf_path = tmp_path / "merge_large.pdf"
    _create_text_pdf(pdf_path, page_count=120)

    doc = fitz.open(pdf_path)
    chapters = [
        Chapter(title="Invalid start", page=0),
        Chapter(title="Out of range", page=999),
        Chapter(title="Segment A", page=1),
        Chapter(title="Duplicate A", page=1),
        Chapter(title="Segment B", page=31),
        Chapter(title="Segment C", page=61),
        Chapter(title="Segment D", page=91),
    ]

    out_path = tmp_path / "merged_large.pdf"
    merge_chapters(doc, chapters, out_path)
    doc.close()

    merged = fitz.open(out_path)
    assert merged.page_count == 120
    merged.close()
