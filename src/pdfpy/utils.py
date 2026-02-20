import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

VERSION = "2.0.0"
CONFIG_FILE_NAME = "chapters_config.md"
MAX_TITLE_LENGTH = 100
TITLE_CLEANUP_REGEX = r'[\\/*?:"><|]'
DEFAULT_OCR_REGEXES = [
    r"^Chapter\s+\d+",
    r"^Section\s+[\d.IVXLCDM]+",
    r"^Part\s+[IVXLCDM\d]+",
    r"^(Appendix|Annex)\s+[A-Z\d]+",
    r"^(Capitulo|Seccion)\s+\d+",
]


@dataclass
class Chapter:
    """Represents a single chapter with a title and starting page."""
    title: str
    page: int


@dataclass
class Config:
    """Configuration for style-based chapter detection."""
    chapter_regex: str = r"^Chapter\s+\d+"
    min_font_size: float = 16.0
    must_be_bold: bool = True
    ocr_regexes: List[str] = field(default_factory=lambda: DEFAULT_OCR_REGEXES.copy())
    ocr_fallback_to_first_page: bool = True
    ocr_render_dpi: int = 300

    @staticmethod
    def from_file(config_path: Path) -> "Config":
        """Parses the chapter style configuration file."""
        config = Config()
        if not config_path.is_file():
            print(f"Info: Configuration file not found at '{config_path}'. Using defaults.")
            return config

        try:
            with config_path.open("r", encoding="utf-8") as file_handle:
                for line in file_handle:
                    if ":" in line and not line.strip().startswith("<!--"):
                        key, value = map(str.strip, line.split(":", 1))
                        if key == "CHAPTER_REGEX":
                            config.chapter_regex = value
                        elif key == "MIN_FONT_SIZE":
                            try:
                                config.min_font_size = float(value)
                            except ValueError:
                                pass
                        elif key == "MUST_BE_BOLD":
                            config.must_be_bold = value.lower() == "true"
                        elif key == "OCR_REGEXES":
                            regexes = [item.strip() for item in value.split("||") if item.strip()]
                            if regexes:
                                config.ocr_regexes = regexes
                        elif key == "OCR_FALLBACK_TO_FIRST_PAGE":
                            config.ocr_fallback_to_first_page = value.lower() == "true"
                        elif key == "OCR_RENDER_DPI":
                            try:
                                dpi = int(value)
                                if dpi > 0:
                                    config.ocr_render_dpi = dpi
                            except ValueError:
                                pass
        except Exception as error:
            print(f"Warning: Could not parse configuration file. Error: {error}")

        return config


def is_chapter_title(text: str, span: dict, pattern: re.Pattern, config: Config) -> bool:
    """Checks if a text span matches the chapter title criteria."""
    is_large_enough = span["size"] >= config.min_font_size
    is_bold = "bold" in span["font"].lower()
    bold_ok = not config.must_be_bold or is_bold
    matches_pattern = pattern.match(text)
    return is_large_enough and bold_ok and bool(matches_pattern)
