# PDF Renaming Tool

Automatically rename PDF files based on their content using NLP techniques. Extracts titles and keywords to generate meaningful filenames — no manual renaming required.

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Tests](https://img.shields.io/badge/Tests-95%20passing-brightgreen)

## Features

- **Content-based renaming** — Extracts titles or top keywords from PDF text
- **Multi-language support** — English, German, and Turkish with language-specific tokenization
- **Smart German handling** — Preserves umlauts (`ä`, `ö`, `ü`, `ß`) with optional ASCII transliteration
- **Collision-safe** — Automatically handles duplicate filenames with incrementing suffixes
- **Dry-run mode** — Preview changes before applying them
- **SOLID architecture** — Modular, testable, and extensible design

## Quick Start

### Prerequisites

- Python 3.12 or higher
- A directory containing PDF files

### Installation

Choose your preferred package manager:

#### Option 1: pip (recommended for most users)

```bash
# Clone the repository
git clone https://github.com/CodingWithMK/pdf_renaming-tool.git
cd pdf_renaming-tool

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install the package
pip install -e .

# Download required NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger_eng')"
```

#### Option 2: uv (faster, for users familiar with uv)

> **New to uv?** [uv](https://docs.astral.sh/uv/) is a fast Python package manager written in Rust. Install it first:
>
> ```bash
> # Install uv (one-time setup)
> curl -LsSf https://astral.sh/uv/install.sh | sh
> # Or on macOS: brew install uv
> # Or on Windows: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
> ```

```bash
# Clone the repository
git clone https://github.com/CodingWithMK/pdf_renaming-tool.git
cd pdf-renaming-tool

# uv automatically creates a virtual environment and installs dependencies
uv sync

# Download required NLTK data
uv run python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger_eng')"
```

## Usage

### Basic Usage

```bash
# Rename all PDFs in a directory
pdf-renaming-tool ./my-pdfs

# Or run directly with Python
python main.py ./my-pdfs
```

### Command-Line Options

```
usage: pdf-renaming-tool [-h] [-n MAX_PAGES] [-d] [-v] [--transliterate-german]
                         [--log-file PATH]
                         directory

Rename PDF files based on content analysis (titles, keywords).

positional arguments:
  directory             Directory containing PDF files to rename.

options:
  -h, --help            Show this help message and exit.
  -n, --max-pages N     Maximum number of pages to extract text from (default: 3).
  -d, --dry-run         Simulate renames without modifying files.
  -v, --verbose         Enable detailed logging output.
  --transliterate-german
                        Convert German umlauts (ae, oe, ue, ss) in filenames.
  --log-file PATH       Write log output to the specified file.
```

### Examples

```bash
# Preview changes without modifying files (recommended first run)
pdf-renaming-tool ./pdfs --dry-run --verbose

# Process deeper into documents (5 pages instead of 3)
pdf-renaming-tool ./pdfs --max-pages 5

# Convert German umlauts to ASCII for compatibility
pdf-renaming-tool ./pdfs --transliterate-german

# Save a log of all operations
pdf-renaming-tool ./pdfs --log-file rename.log
```

### Example Output

```
2025-01-15 10:30:45 [INFO] src.cli: PDF Renaming Tool
2025-01-15 10:30:45 [INFO] src.cli: ========================================
2025-01-15 10:30:45 [INFO] src.cli: Directory:    /home/user/pdfs
2025-01-15 10:30:45 [INFO] src.cli: Max pages:    3
2025-01-15 10:30:45 [INFO] src.cli: Dry run:      False
2025-01-15 10:30:45 [INFO] src.cli: ========================================
2025-01-15 10:30:45 [INFO] src.pdf_renamer.orchestrator: Found 5 PDF files in /home/user/pdfs
2025-01-15 10:30:46 [INFO] src.pdf_renamer.processing.renamer: Renamed: document1.pdf -> Machine_Learning_Algorithms.pdf
2025-01-15 10:30:46 [INFO] src.pdf_renamer.processing.renamer: Renamed: doc2.pdf -> Datenstrukturen.pdf
2025-01-15 10:30:47 [INFO] src.cli: 
2025-01-15 10:30:47 [INFO] src.cli: Summary:
2025-01-15 10:30:47 [INFO] src.cli:   Total PDFs found: 5
2025-01-15 10:30:47 [INFO] src.cli:   Renamed:          4
2025-01-15 10:30:47 [INFO] src.cli:   Skipped:          1
```

## How It Works

```
PDF File → Extract Text → Detect Language → Try Title Extraction
                                                      ↓
                                              Title Found?
                                             /            \
                                           Yes             No
                                            ↓               ↓
                                     Slugify Title    Tokenize & Filter
                                            ↓               ↓
                                            ↓         Get Top Keywords
                                            ↓               ↓
                                            └───────┬───────┘
                                                    ↓
                                            Rename File
```

### Renaming Strategies

1. **Title-based** (preferred) — Extracts the most likely title from the first pages
2. **Keyword-based** (fallback) — Uses the most distinctive word from the content

### Supported Languages

| Language | Tokenizer | Stopwords | Special Handling |
|----------|-----------|-----------|------------------|
| English | POS tagging (nouns) | 30+ academic terms | Figure/table filtering |
| German | Frequency-based | 150+ terms (articles, prepositions) | Umlaut preservation, compound words |
| Turkish | Frequency-based | 35+ terms | Turkish character support |

## Architecture

The project follows SOLID principles with clean separation of concerns:

```
src/
├── pdf_renamer/
│   ├── extraction/      # Text extraction (PDF, future: OCR)
│   ├── language/        # Language detection
│   ├── tokenization/    # Multi-language tokenization
│   ├── naming/          # Filename generation strategies
│   ├── processing/      # File operations and pipeline
│   ├── orchestrator.py  # Batch processing
│   └── container.py     # Dependency injection
└── cli/                 # Command-line interface
```

For detailed architecture documentation, see [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Development

### Setting Up Development Environment

```bash
# Clone and enter the repository
git clone https://github.com/yourusername/pdf-renaming-tool.git
cd pdf-renaming-tool

# Install with development dependencies
uv sync --extra dev

# Or with pip
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_tokenizers.py

# Run specific test
pytest tests/unit/test_tokenizers.py::TestGermanTokenizer::test_tokenize_umlauts -v
```

### Code Quality

```bash
# Format code
ruff format .

# Lint and auto-fix
ruff check --fix .

# Type checking
mypy src/
```

### Project Structure

```
.
├── src/
│   ├── pdf_renamer/     # Core library
│   └── cli/             # CLI interface
├── tests/
│   └── unit/            # Unit tests
├── docs/                # Documentation
├── main.py              # Entry point
└── pyproject.toml       # Project configuration
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Write tests for your changes
4. Ensure all tests pass (`pytest`)
5. Ensure code quality (`ruff check . && ruff format .`)
6. Commit your changes (`git commit -m 'Add my feature'`)
7. Push to the branch (`git push origin feature/my-feature`)
8. Open a Pull Request

### Adding Support for a New Language

1. Create `src/pdf_renamer/tokenization/yourlanguage.py`:
   ```python
   from src.pdf_renamer.tokenization.base import Tokenizer
   
   class YourLanguageTokenizer(Tokenizer):
       def tokenize(self, text: str) -> list[str]:
           # Implement tokenization
           ...
   ```

2. Add custom stopwords to `src/pdf_renamer/tokenization/stopwords.py`

3. Register in `src/pdf_renamer/container.py`:
   ```python
   registry.register("xx", YourLanguageTokenizer())
   ```

4. Add tests in `tests/unit/test_tokenizers.py`

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `LookupError: Resource not found` | Run NLTK download commands from installation |
| No text extracted | PDF may be scanned/image-based (OCR not yet supported) |
| Wrong language detected | Use `--verbose` to see detected language; contribute better heuristics |
| Permission denied | Ensure you have write permissions to the PDF directory |

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [NLTK](https://www.nltk.org/) for natural language processing
- [PyPDF2](https://pypdf2.readthedocs.io/) for PDF text extraction
- [langdetect](https://github.com/Mimino666/langdetect) for language detection
