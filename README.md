# PDF Renaming Tool

Production-ready tool that renames PDF files based on content analysis. Reads
the first few pages, extracts or infers a title, applies language-aware
processing, and writes a filesystem-safe filename. Supports English, German,
and Turkish with automatic transliteration for German characters (ä→ae, ö→oe,
ü→ue, ß→ss).

## Overview

The tool processes PDFs in two phases:
1. **Title extraction** — attempts to find a suitable title from the first pages.
2. **Fallback** — if no title is found, extracts the most frequent keywords
   after filtering language-specific stopwords.

Language detection is automatic (via langdetect); processing strategies
(stopwords, tokenizers, keyword extraction) adapt to the detected language.
All filenames are sanitized for filesystem safety and collision-resistant.

## Key Features

- **Monolithic design**: Single file (`pdf_renamer.py`, 1181 lines) with no
  external module dependencies beyond runtime libraries.
- **Language support**: English, German, Turkish with 160, 49, and 36 stopwords
  respectively; German umlauts are transliterated automatically.
- **Intelligent fallback**: Tries title extraction first; uses keyword extraction
  (frequency-based for German/Turkish, POS-based for English) as backup.
- **Safety hardened**: Path traversal detection, filename sanitization, resource
  limits (file size, text length, directory size), Windows reserved name handling.
- **Dry-run mode**: Simulates renames without modifying files.
- **Progress tracking**: Uses `tqdm` for batch processing feedback.

## Quick Start

### Install dependencies

```bash
pip install pypdf langdetect nltk tqdm
```

### Download NLTK data (optional; auto-downloaded on first run)

```bash
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"
```

### Usage

```bash
# Basic dry-run
python pdf_renamer.py ./pdfs --dry-run

# Rename up to 5 pages per file, verbose logging
python pdf_renamer.py ./pdfs -n 5 -v

# Save log to file
python pdf_renamer.py ./pdfs --log-file rename.log

# See all options
python pdf_renamer.py --help
```

**Options:**
- `-n, --max-pages` — maximum pages to extract per PDF (default: 3)
- `-d, --dry-run` — simulate renames without modifying files
- `-v, --verbose` — enable DEBUG-level logging
- `--log-file` — write logs to a file

## Architecture

### Core Components

| Component | Purpose |
|-----------|---------|
| `PdfTextExtractor` | Reads PDF pages using pypdf/PyPDF2 |
| `LanguageDetector` | Detects language with langdetect; falls back to English |
| `TitleExtractor` | Finds a candidate title from first pages |
| `{English,German,Turkish}Tokenizer` | Language-specific word tokenization (NLTK) |
| `TokenizerRegistry` | Maps languages to tokenizers |
| `{English,German,Turkish}KeywordExtractor` | Frequency or POS-based keyword selection |
| `Slugifier` | Sanitizes and transliterates text for filenames |
| `FileRenamer` | Handles renames and collision resolution (with dry-run support) |
| `PdfProcessingPipeline` | Orchestrates per-file processing (extraction → detection → naming) |
| `PdfRenamerOrchestrator` | Batch runner; discovers PDFs and coordinates processing stats |

### Language-Specific Behavior

- **English**: POS tagging to extract nouns; basic stopword filtering
- **German**: Frequency-based extraction; 160 stopwords (core + document); all
  umlauts automatically transliterated (ä→ae, ö→oe, ü→ue, ß→ss)
- **Turkish**: Frequency-based extraction; 49 stopwords; optional transliteration
  (ç→c, ğ→g, etc.; 12 mappings) if enabled

### Error Handling & Limits

- **Exceptions**: `PDFProcessingError`, `PathValidationError`, `ResourceExhaustedError`,
  `NLTKResourceError`
- **Resource limits** (configurable via `ResourceLimits`):
  - Max file size: 100 MB
  - Max extracted text: 1,000,000 chars
  - Max pages per file: 1,000
  - Max files per directory: 10,000

## File Structure

```
.
├── pdf_renamer.py              # Main implementation (1181 lines)
├── test_pdf_renamer.py         # Root-level tests (494 lines)
├── main.py                     # Minimal placeholder
├── __init__.py                 # Package marker
├── pyproject.toml              # Project metadata
├── .gitignore                  # Excludes docs/, pdfs/, venv, etc.
├── .python-version             # Python version specification
└── uv.lock                     # Lockfile for uv package manager
```

### Tests

A comprehensive test suite exists in `test_pdf_renamer.py`:
- 43 passing tests covering stopwords, path validation, tokenization, title
  extraction, slugification, renaming, and pipeline integration.
- Uses pytest fixtures and unittest.mock for isolation.

## Testing

```bash
pytest test_pdf_renamer.py -v
# or
python test_pdf_renamer.py
```

## Development Notes

- **Type hints**: Full PEP 484 coverage (Python 3.12+)
- **Protocols**: Internal use of Protocol (PEP 544) for extensibility
  (`TextExtractor`, `Tokenizer`, `KeywordExtractor`)
- **Dataclasses**: Used for configuration (`ProcessingConfig`, `ResourceLimits`)
- **No external refactoring**: Monolithic by design; all functionality in one file
  for ease of deployment and maintenance.

## Roadmap

Potential enhancements (not yet implemented):
- GitHub Actions CI/CD workflow
- Pre-commit hooks for code quality
- Support for additional languages (French, Spanish)
- Encrypted PDF handling
- Batch status persistence (processed files log)

## Requirements

- Python 3.12+
- Runtime: `pypdf`, `langdetect`, `nltk`, `tqdm`
- Development: `pytest` (for testing)

See `pyproject.toml` for current versions.
