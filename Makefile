.PHONY: install test lint benchmark release verify-release space demo

install:
	pip install -e ".[dev,space]"

test:
	pytest

lint:
	ruff check .

benchmark:
	python scripts/run_benchmark.py

release:
	python scripts/build_release_archive.py

verify-release:
	python scripts/verify_clean_install.py

space:
	python space/app.py

demo:
	agent-atlas demo --out artifacts/demo-report.json
