.PHONY: install lint test build serve clean

install:
	pip install -e .[dev]

lint:
	ruff check src tests

test:
	pytest -q

build:
	python -m statute_watch build

serve: build
	python -m http.server -d dist 8000

clean:
	rm -rf dist build *.egg-info .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
