#!/bin/bash
# Executes the script in MANUAL mode.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}/../src:${PYTHONPATH}"

if [ -z "$1" ]; then
    echo "ERROR: Please provide a PDF file path as an argument."
    echo "Usage: ./run_manual.sh path/to/document.pdf"
    exit 1
fi

echo "--- PDFPy Manual Splitter ---"
echo "Processing: $(basename "$1")"
echo ""

echo "Please enter the starting page number for each chapter, separated by commas."
read -p "Example: 5,10,56: " pages

if [ -z "$pages" ]; then
    echo "ERROR: No page numbers were entered. Aborting."
    exit 1
fi
echo ""

python3 -m pdfpy "$1" --manual "$pages"

echo ""
echo "Script execution finished."
