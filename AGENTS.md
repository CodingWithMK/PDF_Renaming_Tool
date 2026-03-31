AGENTS - Repository Agent Guidelines

Purpose
- This file tells automated coding agents (and humans) how to build, run, lint, test, and make
  consistent code changes in this repository. Keep guidance pragmatic and machine-readable.

Repository quick facts
- Project root: `.`
- Key modules: `src/pdf_renamer/` (core library), `src/cli/` (CLI), `main.py` (entrypoint)
- Python version: `pyproject.toml` requires Python >= 3.12
- Architecture: SOLID-compliant with dependency injection

1) Environment and setup

Using pip:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Using uv (recommended):
```bash
uv sync --extra dev
```

NLTK downloads (run once):
```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger_eng')"
```

2) Run the program

CLI entry points:
```bash
# Using installed script
pdf-renaming-tool ./pdfs --dry-run --verbose

# Or directly
python main.py ./pdfs
```

Key CLI options:
- `--dry-run` / `-d`: Preview without modifying files
- `--verbose` / `-v`: Detailed logging
- `--max-pages N` / `-n N`: Pages to extract (default: 3)
- `--transliterate-german`: Convert umlauts to ASCII

3) Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=src --cov-report=term-missing
```

Run a single test file:
```bash
pytest tests/unit/test_tokenizers.py
```

Run a single test:
```bash
pytest tests/unit/test_tokenizers.py::TestGermanTokenizer::test_tokenize_umlauts -v
```

Run tests matching pattern:
```bash
pytest -k "german" -v
```

4) Linting & formatting

```bash
# Lint and auto-fix
ruff check --fix .

# Format code
ruff format .

# Type checking
mypy src/
```

5) Code style guidelines

- Imports: Use three-section order (stdlib, third-party, local) with single blank lines
- Typing: Add type hints to all public functions; use `from __future__ import annotations`
- Naming: `snake_case` (functions/vars), `PascalCase` (classes), `UPPER_SNAKE_CASE` (constants)
- Error handling: Use `logging` instead of `print()`; avoid bare `except:`
- Paths: Use `pathlib.Path` over `os.path`
- Tests: Mirror module structure under `tests/unit/`; use pytest fixtures and mocks

6) Architecture

```
src/
├── pdf_renamer/
│   ├── extraction/     # TextExtractor ABC + PdfTextExtractor
│   ├── language/       # LanguageDetector ABC + LangdetectDetector
│   ├── tokenization/   # Tokenizer ABC + EN/TR/DE implementations + Registry
│   ├── naming/         # NamingStrategy ABC + Title/Keyword + Slugifier
│   ├── processing/     # FileRenamer + PdfProcessor pipeline
│   ├── orchestrator.py # Batch processing (RenamerOrchestrator)
│   ├── container.py    # Dependency injection wiring
│   └── models.py       # Data classes
├── cli/                # argparse CLI interface
```

SOLID principles:
- SRP: Each module has one responsibility
- OCP: New languages via registry.register(), not modification
- LSP: All ABCs are substitutable
- DIP: Container wires dependencies

7) Adding a new language

1. Create `src/pdf_renamer/tokenization/yourlang.py` extending `Tokenizer`
2. Add stopwords to `src/pdf_renamer/tokenization/stopwords.py`
3. Register in `src/pdf_renamer/container.py`: `registry.register("xx", YourLangTokenizer())`
4. Add tests in `tests/unit/test_tokenizers.py`

8) Making changes (agent workflow)

1. Run linters (`ruff check . && ruff format .`) and fix issues
2. Write/update tests under `tests/unit/` and run `pytest`
3. Make small, focused commits with descriptive messages
4. Do not commit `.venv/` or `__pycache__/`

9) Troubleshooting

- Empty text extracted: PDF may be scanned/image (OCR not supported)
- NLTK LookupError: Run NLTK download commands from setup
- Permission errors: Ensure write access to target directory

Files referenced: `pyproject.toml`, `src/pdf_renamer/`, `src/cli/`, `main.py`, `tests/`
