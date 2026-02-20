import pytest
import fitz
from pathlib import Path
from pdfpy import Chapter, perform_split, merge_chapters

@pytest.fixture
def dummy_pdf(tmp_path):
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    for i in range(10):
        page = doc.new_page()
        page.insert_text((50, 50), f"Page {i+1}")
    doc.save(pdf_path)
    doc.close()
    return pdf_path

def test_perform_split(dummy_pdf, tmp_path):
    doc = fitz.open(dummy_pdf)
    chapters = [
        Chapter(title="Chapter 1", page=1),
        Chapter(title="Chapter 2", page=5),
    ]
    out_dir = tmp_path / "out"
    perform_split(doc, chapters, out_dir)
    doc.close()

    assert (out_dir / "01_Chapter_1.pdf").exists()
    assert (out_dir / "02_Chapter_2.pdf").exists()
    
    # Check page counts
    d1 = fitz.open(out_dir / "01_Chapter_1.pdf")
    assert d1.page_count == 4 # Pages 1, 2, 3, 4
    d1.close()
    
    d2 = fitz.open(out_dir / "02_Chapter_2.pdf")
    assert d2.page_count == 6 # Pages 5, 6, 7, 8, 9, 10
    d2.close()

def test_merge_chapters(dummy_pdf, tmp_path):
    doc = fitz.open(dummy_pdf)
    chapters = [
        Chapter(title="Chapter 1", page=2),
        Chapter(title="Chapter 2", page=8),
    ]
    out_path = tmp_path / "merged.pdf"
    merge_chapters(doc, chapters, out_path)
    doc.close()

    assert out_path.exists()
    d_merged = fitz.open(out_path)
    # Chapter 1: Pages 2-7 (6 pages)
    # Chapter 2: Pages 8-10 (3 pages)
    # Total: 9 pages
    assert d_merged.page_count == 9
    d_merged.close()
