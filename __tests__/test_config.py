from pdfpy import Config


def test_config_defaults():
    config = Config()
    assert config.chapter_regex == r"^Chapter\s+\d+"
    assert config.min_font_size == 16.0
    assert config.must_be_bold is True
    assert r"^Chapter\s+\d+" in config.ocr_regexes
    assert config.ocr_fallback_to_first_page is True
    assert config.ocr_render_dpi == 300


def test_config_from_file(tmp_path):
    config_file = tmp_path / "test_config.md"
    content = """
CHAPTER_REGEX: ^Section\\s+\\d+
MIN_FONT_SIZE: 12
MUST_BE_BOLD: false
OCR_REGEXES: ^Part\\s+[IVXLCDM]+ || ^Appendix\\s+[A-Z]
OCR_FALLBACK_TO_FIRST_PAGE: false
OCR_RENDER_DPI: 400
"""
    config_file.write_text(content)
    config = Config.from_file(config_file)
    assert config.chapter_regex == r"^Section\s+\d+"
    assert config.min_font_size == 12.0
    assert config.must_be_bold is False
    assert config.ocr_regexes == [r"^Part\s+[IVXLCDM]+", r"^Appendix\s+[A-Z]"]
    assert config.ocr_fallback_to_first_page is False
    assert config.ocr_render_dpi == 400


def test_config_partial_file(tmp_path):
    config_file = tmp_path / "test_config_partial.md"
    content = """
MIN_FONT_SIZE: 14
"""
    config_file.write_text(content)
    config = Config.from_file(config_file)
    assert config.chapter_regex == r"^Chapter\s+\d+"
    assert config.min_font_size == 14.0
    assert config.must_be_bold is True
    assert config.ocr_fallback_to_first_page is True
    assert config.ocr_render_dpi == 300


def test_config_invalid_file(tmp_path):
    # Should use defaults if file missing
    config = Config.from_file(tmp_path / "nonexistent.md")
    assert config.chapter_regex == r"^Chapter\s+\d+"
    assert config.min_font_size == 16.0
    assert config.must_be_bold is True
    assert config.ocr_fallback_to_first_page is True
    assert config.ocr_render_dpi == 300
