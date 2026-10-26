.PHONY: clean build docs docs-serve format lint check test

clean:
	rm -rf build dist .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov

build:
	uv build

docs: ## build the MkDocs documentation site
	uv run mkdocs build

docs-serve: ## preview documentation with live reload
	uv run mkdocs serve


format:
	uv run ruff check --fix src tests
	uv run ruff format src tests

lint:
	uv run ruff check src tests

check:
	uv run mypy src

test:
	uv run pytest

