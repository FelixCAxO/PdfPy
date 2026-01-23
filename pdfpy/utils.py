import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

VERSION = "2.0.0"
CONFIG_FILE_NAME = "chapters_config.md"
MAX_TITLE_LENGTH = 100
TITLE_CLEANUP_REGEX = r'[\\/*?:"><|]'


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


def is_chapter_title(text: str, span: dict, pattern: re.Pattern, config: Config) -> bool:
    """Checks if a text span matches the chapter title criteria."""
    is_large_enough = span["size"] >= config.min_font_size
    is_bold = "bold" in span["font"].lower()
    bold_ok = not config.must_be_bold or is_bold
    matches_pattern = pattern.match(text)
    return is_large_enough and bold_ok and bool(matches_pattern)
