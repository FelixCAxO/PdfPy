#!/bin/bash
# Executes the script in AUTOMATIC mode.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export PYTHONPATH="${SCRIPT_DIR}/../src:${PYTHONPATH}"

if [ -z "$1" ]; then
    echo "ERROR: Please provide a PDF file path as an argument."
    echo "Usage: ./run_auto.sh path/to/document.pdf"
    exit 1
fi

echo "--- PDFPy Automatic Splitter ---"
echo "Processing: $(basename "$1")"
echo ""

python3 -m pdfpy "$1"

echo ""
echo "Script execution finished."
