import argparse
from pathlib import Path

import fitz

from .utils import VERSION, CONFIG_FILE_NAME
from .core import process_pdf_manual, process_pdf_automatic, merge_chapters, perform_split


def main() -> None:
    """Entry point for the command-line application."""
    parser = argparse.ArgumentParser(description="Split a PDF document into chapters.")
    parser.add_argument("pdf_file", type=Path, nargs='?', help="Path to the source PDF file.")
    parser.add_argument(
        "--manual",
        metavar="PAGES",
        type=str,
        help="Provide a comma-separated list of starting page numbers.",
    )
    parser.add_argument(
        "--merge",
        action="store_true",
        help="Merge the found sections into a single PDF instead of splitting.",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Enable OCR fallback for scanned/image-based PDFs (requires Tesseract + pytesseract + Pillow).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show the version of the script and exit."
    )
    args = parser.parse_args()

    if not args.pdf_file:
        parser.print_help()
        return

    pdf_path: Path = args.pdf_file

    if not pdf_path.is_file() or pdf_path.suffix.lower() != '.pdf':
        print(f"Error: Path '{pdf_path}' is not a valid PDF file.")
        return

    # Look for config in the same directory as the package or CWD?
    # Original code looked in script_dir = Path(__file__).parent.resolve()
    # which would be src/pdfpy/
    script_dir = Path(__file__).parent.resolve()
    config_file = script_dir / CONFIG_FILE_NAME

    # Handle output path
    if args.merge:
        output_dest = pdf_path.parent / f"{pdf_path.stem}_merged.pdf"
    else:
        output_dest = pdf_path.parent / f"{pdf_path.stem}_chapters"

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error: Could not read '{pdf_path}'. Reason: {e}")
        return

    chapters_to_split = []
    if args.manual is not None:
        print("Running in Manual Mode...")
        chapters_to_split = process_pdf_manual(args.manual)
    else:
        print("Running in Automatic Mode...")
        chapters_to_split = process_pdf_automatic(doc, config_file, allow_ocr=args.ocr)

    if chapters_to_split:
        if args.merge:
            merge_chapters(doc, chapters_to_split, output_dest)
        else:
            perform_split(doc, chapters_to_split, output_dest)
    else:
        print("No valid chapters found or an error occurred.")

    doc.close()
    print("\nProcessing complete.")


if __name__ == '__main__':
    main()
