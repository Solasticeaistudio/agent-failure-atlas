.PHONY: install test lint benchmark space demo

install:
	pip install -e ".[dev,space]"

test:
	pytest

lint:
	ruff check .

benchmark:
	python scripts/run_benchmark.py

space:
	python space/app.py

demo:
	agent-atlas demo --out artifacts/demo-report.json
