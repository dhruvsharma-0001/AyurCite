.PHONY: install ingest test eval serve clean

PYTHON := PYTHONPATH=. .venv/bin/python
PYTEST := PYTHONPATH=. .venv/bin/pytest
UVICORN := .venv/bin/uvicorn

install:
	@which uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	uv venv --python 3.11 .venv
	uv pip install --python .venv/bin/python -e ".[dev]"

ingest:
	$(PYTHON) scripts/01_acquire.py
	$(PYTHON) scripts/03_segment.py
	$(PYTHON) scripts/05_qa_corpus.py

test:
	$(PYTEST) tests/ -v

eval:
	$(PYTHON) evals/run_eval.py --mock-llm

serve:
	$(UVICORN) src.ayurcite.api.main:app --host 0.0.0.0 --port 8000 --reload

clean:
	rm -rf __pycache__ .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
