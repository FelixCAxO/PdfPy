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
    assert process_pdf_manual("   ") == []


def test_process_pdf_manual_invalid():
    assert process_pdf_manual("abc") is None
    assert process_pdf_manual("2,three,5") is None


def test_process_pdf_manual_rejects_non_positive_pages():
    assert process_pdf_manual("0,3") is None
    assert process_pdf_manual("-2,5") is None


def test_process_pdf_manual_ignores_empty_tokens():
    chapters = process_pdf_manual("1, 3, ")
    assert len(chapters) == 2
    assert chapters[0].page == 1
    assert chapters[1].page == 3

    chapters = process_pdf_manual("1,,3")
    assert len(chapters) == 2
    assert chapters[0].page == 1
    assert chapters[1].page == 3


def test_process_pdf_manual_sorts_and_deduplicates():
    chapters = process_pdf_manual("8, 3, 8, 5")
    assert [chapter.page for chapter in chapters] == [3, 5, 8]


def test_process_pdf_manual_only_commas_is_empty():
    assert process_pdf_manual(",,,") == []

