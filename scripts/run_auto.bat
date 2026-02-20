@echo off
setlocal

set "PYTHONPYCACHEPREFIX=%~dp0..\.cache\pycache"
set "PYTHONPATH=%~dp0..\src;%PYTHONPATH%"

if "%~1"=="" (
    echo ERROR: To use this script, drag and drop a single PDF file onto it.
    pause
    exit /b
)

echo --- PDFPy Automatic Splitter ---
echo Processing: "%~nx1"
echo.

python -m pdfpy "%~1"

echo.
echo Script execution finished.
pause
endlocal