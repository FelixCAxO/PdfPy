@echo off
REM Executes the script in MANUAL mode. Drag a PDF onto this file.

if "%~1"=="" (
    echo ERROR: To use this script, drag and drop a single PDF file onto it.
    pause
    exit /b
)

echo --- PDFPy Manual Splitter ---
echo Processing: "%~nx1"
echo.

echo Please enter the starting page number for each chapter, separated by commas.
set /p pages="Example: 5,10,56: "
if "%pages%"=="" (
    echo ERROR: No page numbers were entered. Aborting.
    pause
    exit /b
)
echo.

python -m pdfpy "%~1" --manual "%pages%"

echo.
echo Script execution finished.
pause
