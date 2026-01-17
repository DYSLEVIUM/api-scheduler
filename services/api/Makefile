.PHONY: help install run test test-unit test-integration clean

UV := uv
PYTHON := $(UV) run python
APP := src/main.py
TEST_DIR := src/tests

help:
	@echo "Available targets:"
	@echo "  make install       - Install dependencies"
	@echo "  make run           - Run the application"
	@echo "  make test          - Run all tests"
	@echo "  make test-unit     - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make clean         - Clean cache files"

install:
	$(UV) sync

run:
	$(UV) run uvicorn main:app --host 0.0.0.0 --port 8000 --reload --app-dir src

test:
	$(UV) run pytest $(TEST_DIR) -v

test-unit:
	$(UV) run pytest $(TEST_DIR)/unit -v

test-integration:
	$(UV) run pytest $(TEST_DIR)/integration -v

clean:
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
