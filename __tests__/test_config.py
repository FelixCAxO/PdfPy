import pytest
from pathlib import Path
from pdfpy import Config

def test_config_defaults():
    config = Config()
    assert config.chapter_regex == r'^Chapter\s+\d+'
    assert config.min_font_size == 16.0
    assert config.must_be_bold is True

def test_config_from_file(tmp_path):
    config_file = tmp_path / "test_config.md"
    content = """
CHAPTER_REGEX: ^Section\\s+\\d+
MIN_FONT_SIZE: 12
MUST_BE_BOLD: false
"""
    config_file.write_text(content)
    config = Config.from_file(config_file)
    assert config.chapter_regex == r'^Section\s+\d+'
    assert config.min_font_size == 12.0
    assert config.must_be_bold is False

def test_config_partial_file(tmp_path):
    config_file = tmp_path / "test_config_partial.md"
    content = """
MIN_FONT_SIZE: 14
"""
    config_file.write_text(content)
    config = Config.from_file(config_file)
    assert config.chapter_regex == r'^Chapter\s+\d+'
    assert config.min_font_size == 14.0
    assert config.must_be_bold is True

def test_config_invalid_file(tmp_path):
    # Should use defaults if file missing
    config = Config.from_file(tmp_path / "nonexistent.md")
    assert config.chapter_regex == r'^Chapter\s+\d+'
    assert config.min_font_size == 16.0
