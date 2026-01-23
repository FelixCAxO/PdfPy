import pytest
from pdfpy import process_pdf_manual

def test_process_pdf_manual_multiple():
    chapters = process_pdf_manual("5,10,15")
    assert len(chapters) == 3
    assert chapters[0].page == 5
    assert chapters[1].page == 10
    assert chapters[2].page == 15
    assert chapters[0].title == "Section_Page_5"

def test_process_pdf_manual_single_page_one():
    chapters = process_pdf_manual("1")
    assert len(chapters) == 1
    assert chapters[0].page == 1

def test_process_pdf_manual_single_page_greater_than_one():
    # New behavior: if "10" is given, it should return [1, 10]
    chapters = process_pdf_manual("10")
    assert len(chapters) == 2
    assert chapters[0].page == 1
    assert chapters[1].page == 10

def test_process_pdf_manual_empty():
    assert process_pdf_manual("") == []
    assert process_pdf_manual(None) == []

def test_process_pdf_manual_invalid():
    assert process_pdf_manual("abc") is None
