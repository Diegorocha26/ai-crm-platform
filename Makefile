.PHONY: setup sync test test-unit test-integration api worker worker-enrich clean help

# Default command
help:
	@echo "Available commands:"
	@echo "  make setup            - Full project setup (uv sync + playwright)"
	@echo "  make sync             - Sync dependencies only"
	@echo "  make test             - Run all tests"
	@echo "  make test-unit        - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make api              - Run FastAPI server"
	@echo "  make worker-scrape    - Run Scrape worker (requires Linux/WSL/Docker)"
	@echo "  make clean            - Remove cache and temporary files"

setup:
	uv sync
	uv run playwright install chromium

sync:
	uv sync

test:
	uv run pytest

test-unit:
	uv run pytest tests/unit

test-integration:
	uv run pytest tests/integration

api:
	uv run uvicorn api.main:app --reload

worker-scrape:
	uv run rq worker scrape --url redis://localhost:6379

clean:
	rm -rf .pytest_cache .venv build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
