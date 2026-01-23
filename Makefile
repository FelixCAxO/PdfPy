.PHONY: install test clean help

help:
	@echo "Available commands:"
	@echo "  make install  - Install dependencies"
	@echo "  make test     - Run tests"
	@echo "  make clean    - Remove temporary files"

install:
	pip install -r requirements.txt

test:
	python3 -m pytest

clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	rm -rf pdfpy/__pycache__
	rm -rf __tests__/__pycache__
