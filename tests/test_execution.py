import subprocess
import sys
from pathlib import Path

def test_package_execution():
    # Attempt to run the package as a module
    # We expect this to fail currently with the specific error reported by the user
    # unless we are in the 'Red' phase where we WANT it to fail to prove the bug.
    
    # We use -h to just check if the help message appears, 
    # which would indicate successful entry point execution.
    result = subprocess.run(
        [sys.executable, "-m", "pdfpy", "--help"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent)
    )
    
    # In the Red phase, this should fail because __main__.py is missing
    assert result.returncode == 0
    assert "Split a PDF document into chapters" in result.stdout
