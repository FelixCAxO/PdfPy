import pytest
import fitz
import re
from pathlib import Path
from pdfpy import Config, find_chapters_by_style, Chapter, is_chapter_title

@pytest.fixture
def styled_pdf(tmp_path):
    pdf_path = tmp_path / "styled.pdf"
    doc = fitz.open()
    
    # Page 1: Chapter 1
    page = doc.new_page()
    page.insert_text((50, 50), "Chapter 1: Introduction", fontsize=20, fontname="helv")
    
    # Page 2: Normal text
    page = doc.new_page()
    page.insert_text((50, 50), "Some regular text here.", fontsize=12, fontname="helv")
    
    # Page 3: Chapter 2
    page = doc.new_page()
    page.insert_text((50, 50), "Chapter 2: Methods", fontsize=20, fontname="helv")
    
    doc.save(pdf_path)
    doc.close()
    return pdf_path

def test_is_chapter_title():
    config = Config(min_font_size=16, must_be_bold=True)
    pattern = re.compile(config.chapter_regex)
    
    span_ok = {"size": 20, "font": "Helvetica-Bold", "text": "Chapter 1"}
    assert is_chapter_title("Chapter 1", span_ok, pattern, config) is True
    
    span_small = {"size": 12, "font": "Helvetica-Bold", "text": "Chapter 1"}
    assert is_chapter_title("Chapter 1", span_small, pattern, config) is False
    
    span_not_bold = {"size": 20, "font": "Helvetica", "text": "Chapter 1"}
    assert is_chapter_title("Chapter 1", span_not_bold, pattern, config) is False
    
    span_wrong_text = {"size": 20, "font": "Helvetica-Bold", "text": "Introduction"}
    assert is_chapter_title("Introduction", span_wrong_text, pattern, config) is False

def test_find_chapters_by_style(styled_pdf):
    doc = fitz.open(styled_pdf)
    config = Config(min_font_size=18, must_be_bold=False)
    chapters = find_chapters_by_style(doc, config)
    doc.close()
    
    assert len(chapters) == 2
    assert chapters[0].title == "Chapter 1: Introduction"
    assert chapters[0].page == 1
    assert chapters[1].title == "Chapter 2: Methods"
    assert chapters[1].page == 3
