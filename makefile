.PHONY: install format lint type test audit sec hooks up down logs

PY=python3

install:
	@uv pip install -e .[dev] || pip install -e .[dev]
	@echo "Installed dev deps."

format:
	@black .

lint:
	@ruff check .

type:
	@mypy app tests

test:
	@pytest

audit:
	@pip-audit -r || true

sec:
	@bandit -q -r app -x tests || true

hooks:
	@pre-commit install
	@echo "pre-commit hooks installed."

up:
	@docker compose up -d mongo

down:
	@docker compose down

logs:
	@docker compose logs -f mongo


# --- append to your existing Makefile ---

run:
	@uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

