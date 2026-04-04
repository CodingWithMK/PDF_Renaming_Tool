"""
PDF Renaming Tool - Monolithic Implementation

A senior-level, production-ready refactoring of the PDF renaming tool with:
- German language support with comprehensive stopwords
- SOLID-inspired internal architecture
- Security hardening (path validation, resource limits)
- Enhanced error handling and logging
- Extensible design patterns

Author: PDF Renaming Tool Contributors
Version: 0.3.0
"""

from __future__ import annotations

import logging
import os
import re
import string
import sys
from collections import Counter
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import ClassVar, Protocol, TypeVar

from tqdm import tqdm

try:
    from PyPDF2 import PdfReader
except ImportError:
    from pypdf import PdfReader

try:
    from langdetect import detect, LangDetectException
except ImportError:
    detect = None

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk import pos_tag, word_tokenize

    _NLTK_AVAILABLE = True
except ImportError:
    _NLTK_AVAILABLE = False

T = TypeVar("T")


class NLTKResourceError(Exception):
    """Raised when required NLTK resources are not available."""

    pass


class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""

    pass


class PathValidationError(Exception):
    """Raised when path validation fails."""

    pass


class ResourceExhaustedError(Exception):
    """Raised when resource limits are exceeded."""

    pass


# =============================================================================
# Configuration & Constants
# =============================================================================


class SupportedLanguage(Enum):
    """Supported languages for PDF processing."""

    ENGLISH = "en"
    GERMAN = "de"
    TURKISH = "tr"

    @classmethod
    def from_code(cls, code: str) -> SupportedLanguage:
        """Convert language code to enum."""
        try:
            return cls(code)
        except ValueError:
            return cls.ENGLISH


@dataclass(frozen=True)
class ResourceLimits:
    """Configuration for resource limits."""

    max_file_size_mb: int = 100
    max_pages: int = 1000
    max_text_length: int = 1_000_000
    max_directory_files: int = 10000


@dataclass
class ProcessingConfig:
    """Configuration for PDF renaming process."""

    max_pages: int = 3
    dry_run: bool = False
    verbose: bool = False
    log_file: Path | None = None
    resource_limits: ResourceLimits = field(default_factory=ResourceLimits)


# =============================================================================
# German Language Support - Comprehensive Stopwords
# =============================================================================


class GermanStopwords:
    """German stopwords for token filtering."""

    CORE: ClassVar[frozenset[str]] = frozenset(
        {
            "der",
            "die",
            "das",
            "den",
            "dem",
            "des",
            "ein",
            "eine",
            "einem",
            "einen",
            "einer",
            "eines",
            "und",
            "oder",
            "aber",
            "sondern",
            "doch",
            "ist",
            "sind",
            "war",
            "waren",
            "wird",
            "werden",
            "wurde",
            "wurden",
            "auf",
            "an",
            "in",
            "mit",
            "von",
            "zu",
            "fur",
            "bei",
            "nach",
            "aus",
            "sich",
            "ich",
            "du",
            "er",
            "sie",
            "wir",
            "ihr",
            "man",
            "dass",
            "ob",
            "wenn",
            "weil",
            "als",
            "wie",
            "was",
            "wer",
            "wo",
            "auch",
            "noch",
            "schon",
            "nur",
            "sehr",
            "so",
            "da",
            "hier",
            "dort",
            "dann",
            "nun",
            "ja",
            "nein",
            "mal",
            "nicht",
            "kein",
            "keine",
            "keinen",
            "keinem",
            "keiner",
            "uber",
            "unter",
            "zwischen",
            "neben",
            "vor",
            "hinter",
            "alle",
            "jede",
            "jeder",
            "jedes",
            "alles",
            "diese",
            "dieser",
            "dies",
            "diesen",
            "diesem",
            "mehr",
            "andere",
            "anderen",
            "anderer",
            "anderes",
            "kann",
            "konnen",
            "muss",
            "mussen",
            "soll",
            "sollen",
            "will",
            "wollen",
            "darf",
            "durfen",
            "mag",
            "mogen",
            "machen",
            "gehen",
            "kommen",
            "sehen",
            "zwei",
            "drei",
            "vier",
            "funf",
            "sechs",
            "sieben",
            "acht",
            "neun",
            "zehn",
            "jahr",
            "jahre",
            "jahren",
            "zeit",
            "immer",
            "oft",
            "manchmal",
            "selten",
            "nie",
            "bis",
            "seit",
            "wahrend",
            "ohne",
            "gegen",
            "um",
        }
    )

    DOCUMENT: ClassVar[frozenset[str]] = frozenset(
        {
            "kapitel",
            "seite",
            "seiten",
            "bild",
            "tabelle",
            "abbildung",
            "beispiel",
            "siehe",
            "vgl",
            "usw",
            "etc",
            "ca",
            "bzw",
            "durch",
            "damit",
            "dazu",
            "dafur",
            "hierbei",
            "autoren",
            "autor",
            "verfasser",
            "herausgeber",
            "inhaltsverzeichnis",
            "literatur",
            "quellen",
            "abbildungen",
            "tabellen",
        }
    )

    @classmethod
    def get_all(cls) -> set[str]:
        """Get all German stopwords."""
        return cls.CORE | cls.DOCUMENT


class TurkishStopwords:
    """Turkish stopwords for token filtering."""

    CORE: ClassVar[frozenset[str]] = frozenset(
        {
            "icin",
            "olarak",
            "veya",
            "ve",
            "ile",
            "ama",
            "fakat",
            "ancak",
            "gibi",
            "daha",
            "cok",
            "az",
            "her",
            "bir",
            "bu",
            "su",
            "o",
            "da",
            "de",
            "ki",
            "mi",
            "mu",
            "mü",
            "ya",
            "ise",
            "en",
            "sonra",
            "once",
            "kadar",
            "gore",
            "üzere",
            "icinde",
            "üzerine",
            "arasinda",
            "tarafindan",
            "hakkinda",
            "karsi",
            "ic",
            "dis",
            "altinda",
            "üstünde",
            "yaninda",
        }
    )

    DOCUMENT: ClassVar[frozenset[str]] = frozenset(
        {"sekil", "ssekil", "tablo", "kaynak", "referans", "bölüm", "bolum"}
    )

    @classmethod
    def get_all(cls) -> set[str]:
        """Get all Turkish stopwords."""
        return cls.CORE | cls.DOCUMENT


class EnglishStopwords:
    """English stopwords for token filtering."""

    CORE: ClassVar[frozenset[str]] = frozenset()

    DOCUMENT: ClassVar[frozenset[str]] = frozenset(
        {
            "fig",
            "figure",
            "table",
            "page",
            "pages",
            "chapter",
            "etc",
            "ie",
            "eg",
            "also",
            "one",
            "two",
            "three",
            "may",
            "can",
            "must",
            "should",
            "could",
            "would",
            "however",
            "thus",
            "therefore",
            "et",
            "al",
            "use",
            "used",
            "using",
            "based",
            "within",
            "among",
            "per",
            "via",
            "see",
            "shown",
            "solution",
            "solutions",
        }
    )

    @classmethod
    def get_all(cls) -> set[str]:
        """Get all English stopwords."""
        return cls.CORE | cls.DOCUMENT


# =============================================================================
# German Transliteration Mapping
# Used when language == SupportedLanguage.GERMAN
# =============================================================================

GERMAN_TRANSLITERATION: dict[str, str] = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "ß": "ss",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
}

# =============================================================================
# Turkish Transliteration Mapping
# Used when language == SupportedLanguage.TURKISH
# =============================================================================

TURKISH_TRANSLITERATION: dict[str, str] = {
    "ç": "c",
    "Ç": "C",
    "ğ": "g",
    "Ğ": "G",
    "ı": "i",
    "İ": "I",
    "ö": "o",
    "Ö": "O",
    "ş": "s",
    "Ş": "S",
    "ü": "u",
    "Ü": "U",
}


# =============================================================================
# Security & Validation Utilities
# =============================================================================


class PathValidator:
    """Validates file paths for security."""

    @staticmethod
    def validate_safe_path(base_dir: Path, target_path: Path) -> bool:
        """
        Ensure target path is within base directory (prevent path traversal).

        Args:
            base_dir: The base directory that should contain all operations
            target_path: The path to validate

        Returns:
            True if path is safe

        Raises:
            PathValidationError: If path is unsafe
        """
        try:
            resolved_target = target_path.resolve()
            resolved_base = base_dir.resolve()
            resolved_target.relative_to(resolved_base)
            return True
        except ValueError:
            raise PathValidationError(
                f"Path traversal detected: {target_path} is outside {base_dir}"
            )

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename for filesystem safety.

        Args:
            filename: Raw filename to sanitize

        Returns:
            Sanitized filename
        """
        sanitized = "".join(
            char for char in filename if ord(char) >= 32 and char not in '<>:"/\\|?*'
        )

        reserved = {"CON", "PRN", "AUX", "NUL", "COM1", "LPT1"}
        name_without_ext = sanitized.split(".")[0].upper()
        if name_without_ext in reserved:
            sanitized = f"_{sanitized}"

        if len(sanitized) > 200:
            name, ext = (
                sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
            )
            sanitized = f"{name[:200]}.{ext}" if ext else name[:200]

        return sanitized


class ResourceLimiter:
    """Enforces resource limits during processing."""

    def __init__(self, limits: ResourceLimits = ResourceLimits()):
        self._limits = limits

    def validate_file(self, file_path: Path) -> None:
        """
        Validate file against resource limits.

        Args:
            file_path: Path to file to validate

        Raises:
            ResourceExhaustedError: If file exceeds limits
        """
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > self._limits.max_file_size_mb:
            raise ResourceExhaustedError(
                f"File size {size_mb:.1f}MB exceeds limit of {self._limits.max_file_size_mb}MB"
            )

    def validate_text(self, text: str) -> None:
        """
        Validate extracted text against limits.

        Args:
            text: Extracted text to validate

        Raises:
            ResourceExhaustedError: If text exceeds limits
        """
        if len(text) > self._limits.max_text_length:
            raise ResourceExhaustedError(
                f"Text length {len(text)} exceeds limit of {self._limits.max_text_length}"
            )


# =============================================================================
# Abstract Base Classes (Internal Pattern for Extensibility)
# =============================================================================


class TextExtractor(Protocol):
    """Protocol for text extraction from documents."""

    def extract(self, pdf_path: Path, max_pages: int = 3) -> str:
        """Extract text from PDF."""
        ...

    def extract_pages(self, pdf_path: Path, max_pages: int = 3) -> list[str]:
        """Extract text from individual pages."""
        ...


class Tokenizer(Protocol):
    """Protocol for text tokenization."""

    def tokenize(self, text: str) -> list[str]:
        """Tokenize text into words."""
        ...


class KeywordExtractor(Protocol):
    """Protocol for keyword extraction strategies."""

    def extract(self, words: list[str], n: int = 4) -> list[str]:
        """Extract top N keywords."""
        ...


# =============================================================================
# PDF Text Extraction Implementation
# =============================================================================


class PdfTextExtractor:
    """Extracts text from PDF documents."""

    def extract(self, pdf_path: Path, max_pages: int = 3) -> str:
        """Extract concatenated text from first N pages."""
        pages = self.extract_pages(pdf_path, max_pages)
        return "".join(pages)

    def extract_pages(self, pdf_path: Path, max_pages: int = 3) -> list[str]:
        """
        Extract text from individual pages.

        Args:
            pdf_path: Path to PDF file
            max_pages: Maximum number of pages to extract

        Returns:
            List of text strings, one per page

        Raises:
            PDFProcessingError: If PDF cannot be read
        """
        if not pdf_path.exists():
            raise PDFProcessingError(f"PDF file not found: {pdf_path}")

        if pdf_path.stat().st_size == 0:
            raise PDFProcessingError(f"PDF file is empty: {pdf_path}")

        try:
            reader = PdfReader(str(pdf_path))
            total_pages = len(reader.pages)
            pages_to_read = min(total_pages, max_pages)

            pages: list[str] = []
            for i in range(pages_to_read):
                text = reader.pages[i].extract_text()
                pages.append(text or "")

            return pages
        except Exception as e:
            raise PDFProcessingError(f"Error reading {pdf_path}: {e}")


# =============================================================================
# Language Detection Implementation
# =============================================================================


class LanguageDetector:
    """Detects language of text using langdetect."""

    def detect(self, text: str) -> SupportedLanguage:
        """
        Detect language of given text.

        Args:
            text: Text to analyze

        Returns:
            SupportedLanguage enum value
        """
        if not text or not text.strip():
            return SupportedLanguage.ENGLISH

        if detect is None:
            return SupportedLanguage.ENGLISH

        try:
            code = detect(text)
            return SupportedLanguage.from_code(code)
        except (LangDetectException, ValueError):
            return SupportedLanguage.ENGLISH


# =============================================================================
# Title Extraction Implementation
# =============================================================================


class TitleExtractor:
    """Extracts probable title from PDF text."""

    def extract(self, pages: list[str]) -> str | None:
        """
        Extract probable title from first pages.

        Args:
            pages: List of page texts

        Returns:
            Title string if found, None otherwise
        """
        if not pages:
            return None

        lines: list[str] = []
        for page_text in pages:
            if not page_text:
                continue
            page_lines = page_text.split("\n")
            filtered = [line.strip() for line in page_lines if len(line.strip()) >= 6]
            lines.extend(filtered)

        if not lines:
            return None

        probable_titles = [
            line for line in lines if (8 < len(line) < 140) and not line.isupper()
        ]
        if probable_titles:
            return probable_titles[0]

        return max(lines, key=len)


# =============================================================================
# Tokenizer Implementations
# =============================================================================


class BaseTokenizer:
    """Base class for tokenizers with common functionality."""

    def __init__(self, custom_stopwords: set[str] | None = None):
        self._custom_stopwords = custom_stopwords or set()

    def _filter_tokens(self, words: list[str], min_length: int = 4) -> list[str]:
        """Filter tokens by length and alpha check."""
        return [w for w in words if w.isalpha() and len(w) >= min_length]


class EnglishTokenizer(BaseTokenizer):
    """English tokenizer with POS-based keyword extraction."""

    def __init__(self, custom_stopwords: set[str] | None = None):
        super().__init__(custom_stopwords)
        self._stopwords = (
            set(stopwords.words("english"))
            | EnglishStopwords.get_all()
            | self._custom_stopwords
        )

    def tokenize(self, text: str) -> list[str]:
        """Tokenize English text."""
        text = text.lower()
        text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
        words = word_tokenize(text)
        words = [w for w in words if w not in self._stopwords]
        return self._filter_tokens(words)


class GermanTokenizer(BaseTokenizer):
    """German tokenizer with comprehensive stopword filtering."""

    def __init__(self, custom_stopwords: set[str] | None = None):
        super().__init__(custom_stopwords)
        self._stopwords = GermanStopwords.get_all() | self._custom_stopwords

    def tokenize(self, text: str) -> list[str]:
        """Tokenize German text."""
        text = text.lower()
        text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
        words = word_tokenize(text)
        words = [w for w in words if w not in self._stopwords]
        return self._filter_tokens(words)


class TurkishTokenizer(BaseTokenizer):
    """Turkish tokenizer with custom stopwords."""

    def __init__(self, custom_stopwords: set[str] | None = None):
        super().__init__(custom_stopwords)
        self._stopwords = (
            set(stopwords.words("turkish"))
            | TurkishStopwords.get_all()
            | self._custom_stopwords
        )

    def tokenize(self, text: str) -> list[str]:
        """Tokenize Turkish text."""
        text = text.lower()
        text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
        words = word_tokenize(text)
        words = [w for w in words if w not in self._stopwords]
        return self._filter_tokens(words)


# =============================================================================
# Tokenizer Registry
# =============================================================================


class TokenizerRegistry:
    """Registry for mapping languages to tokenizers."""

    def __init__(self):
        self._tokenizers: dict[SupportedLanguage, BaseTokenizer] = {}

    def register(self, lang: SupportedLanguage, tokenizer: BaseTokenizer) -> None:
        """Register a tokenizer for a language."""
        self._tokenizers[lang] = tokenizer

    def get(self, lang: SupportedLanguage) -> BaseTokenizer:
        """Get tokenizer for language, defaulting to English."""
        return self._tokenizers.get(
            lang, self._tokenizers.get(SupportedLanguage.ENGLISH)
        )

    def get_all(self) -> dict[SupportedLanguage, BaseTokenizer]:
        """Get all registered tokenizers."""
        return self._tokenizers.copy()


# =============================================================================
# Keyword Extraction Strategies
# =============================================================================


class EnglishKeywordExtractor:
    """Extracts keywords using POS tagging for English."""

    def extract(self, words: list[str], n: int = 4) -> list[str]:
        """Extract top N nouns using POS tagging."""
        if not words:
            return []
        tagged = pos_tag(words)
        nouns = [word for word, pos in tagged if pos.startswith("NN")]
        counter = Counter(nouns)
        return [word for word, _ in counter.most_common(n)]


class GermanKeywordExtractor:
    """Extracts keywords using frequency for German."""

    def extract(self, words: list[str], n: int = 4) -> list[str]:
        """Extract top N words by frequency."""
        if not words:
            return []
        counter = Counter(words)
        return [word for word, _ in counter.most_common(n)]


class TurkishKeywordExtractor:
    """Extracts keywords using frequency for Turkish."""

    def extract(self, words: list[str], n: int = 4) -> list[str]:
        """Extract top N words by frequency."""
        if not words:
            return []
        counter = Counter(words)
        return [word for word, _ in counter.most_common(n)]


# =============================================================================
# Slugifier Implementation
# =============================================================================


class Slugifier:
    """Converts text to filename-safe strings."""

    def __init__(self, transliterate_turkish: bool = False):
        self._transliterate_turkish = transliterate_turkish

    def slugify(self, text: str, language: SupportedLanguage) -> str:
        """
        Convert text to filename-safe format.

        Args:
            text: Text to convert
            language: Target language for transliteration

        Returns:
            Filename-safe string
        """
        text = text.strip().replace(" ", "_")
        text = PathValidator.sanitize_filename(text)

        # Always transliterate German umlauts for filesystem compatibility
        if language == SupportedLanguage.GERMAN:
            for src, tgt in GERMAN_TRANSLITERATION.items():
                text = text.replace(src, tgt)
        elif language == SupportedLanguage.TURKISH and self._transliterate_turkish:
            for src, tgt in TURKISH_TRANSLITERATION.items():
                text = text.replace(src, tgt)

        return text


# =============================================================================
# File Renamer Implementation
# =============================================================================


class FileRenamer:
    """Handles file renaming with collision detection."""

    def __init__(self, dry_run: bool = False):
        self._dry_run = dry_run

    def rename(
        self, pdf_path: Path, new_name: str, target_dir: Path
    ) -> tuple[Path, bool]:
        """
        Rename PDF file with collision handling.

        Args:
            pdf_path: Original PDF path
            new_name: New filename (without extension)
            target_dir: Target directory

        Returns:
            Tuple of (new_path, success)
        """
        ext = ".pdf"
        new_filename = f"{new_name}{ext}"
        new_path = target_dir / new_filename
        counter = 1

        while new_path.exists():
            new_filename = f"{new_name}_{counter}{ext}"
            new_path = target_dir / new_filename
            counter += 1

        if self._dry_run:
            # In dry-run mode, return the hypothetical new path
            return new_path, True

        try:
            pdf_path.rename(new_path)
            return new_path, True
        except OSError as e:
            logging.error(f"Failed to rename {pdf_path}: {e}")
            return new_path, False


# =============================================================================
# Processing Pipeline
# =============================================================================


class PdfProcessingPipeline:
    """Orchestrates the PDF renaming process."""

    def __init__(self, config: ProcessingConfig):
        self._config = config
        self._extractor = PdfTextExtractor()
        self._language_detector = LanguageDetector()
        self._title_extractor = TitleExtractor()
        self._resource_limiter = ResourceLimiter(config.resource_limits)
        self._renamer = FileRenamer(config.dry_run)

        self._tokenizer_registry = self._build_tokenizer_registry()
        self._keyword_extractors = self._build_keyword_extractors()
        self._slugifier = Slugifier()

    def _build_tokenizer_registry(self) -> TokenizerRegistry:
        """Build and populate the tokenizer registry."""
        registry = TokenizerRegistry()
        registry.register(SupportedLanguage.ENGLISH, EnglishTokenizer())
        registry.register(SupportedLanguage.GERMAN, GermanTokenizer())
        registry.register(SupportedLanguage.TURKISH, TurkishTokenizer())
        return registry

    def _build_keyword_extractors(self) -> dict[SupportedLanguage, KeywordExtractor]:
        """Build keyword extractors for each language."""
        return {
            SupportedLanguage.ENGLISH: EnglishKeywordExtractor(),
            SupportedLanguage.GERMAN: GermanKeywordExtractor(),
            SupportedLanguage.TURKISH: TurkishKeywordExtractor(),
        }

    def process(self, pdf_path: Path) -> tuple[Path | None, str | None]:
        """
        Process a single PDF file.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (new_path or None, reason or None)
        """
        try:
            self._resource_limiter.validate_file(pdf_path)
            pages = self._extractor.extract_pages(pdf_path, self._config.max_pages)
            text = "".join(pages)

            if not text.strip():
                return None, "no_text"

            self._resource_limiter.validate_text(text)

            language = self._language_detector.detect(text)
            title = self._title_extractor.extract(pages)

            if title:
                new_name = self._slugifier.slugify(title, language)
                if new_name:
                    new_path, success = self._renamer.rename(
                        pdf_path, new_name, pdf_path.parent
                    )
                    if success:
                        return new_path, None

            tokenizer = self._tokenizer_registry.get(language)
            words = tokenizer.tokenize(text)

            if not words:
                return None, "no_keywords"

            keyword_extractor = self._keyword_extractors[language]
            top_words = keyword_extractor.extract(words, n=4)

            if top_words:
                top_words_sorted = sorted(top_words, key=lambda w: (-len(w), w))
                new_name = self._slugifier.slugify(top_words_sorted[0], language)
                new_path, success = self._renamer.rename(
                    pdf_path, new_name, pdf_path.parent
                )
                if success:
                    return new_path, None

            return None, "no_suitable_name"

        except ResourceExhaustedError as e:
            logging.warning(f"Resource limit exceeded for {pdf_path}: {e}")
            return None, "resource_limit"
        except PDFProcessingError as e:
            logging.error(f"Processing error for {pdf_path}: {e}")
            return None, "processing_error"
        except Exception as e:
            logging.error(f"Unexpected error processing {pdf_path}: {e}")
            return None, "unexpected_error"


# =============================================================================
# Main Orchestrator
# =============================================================================


class PdfRenamerOrchestrator:
    """Orchestrates batch processing of PDF files."""

    def __init__(self, config: ProcessingConfig):
        self._config = config
        self._pipeline = PdfProcessingPipeline(config)
        self._logger = logging.getLogger(__name__)

    def run(self, directory: Path) -> dict[str, int]:
        """
        Process all PDFs in a directory.

        Args:
            directory: Directory containing PDF files

        Returns:
            Dictionary with processing statistics
        """
        if not directory.is_dir():
            self._logger.error(f"Directory not found: {directory}")
            return {"total": 0, "renamed": 0, "skipped": 0}

        pdf_files = self._discover_files(directory)
        self._logger.info(f"Found {len(pdf_files)} PDF files in {directory}")

        stats = {"total": len(pdf_files), "renamed": 0, "skipped": 0}

        for pdf_file in tqdm(pdf_files, desc="Processing PDFs"):
            new_path, reason = self._pipeline.process(pdf_file)
            if new_path is not None:
                self._logger.info(f"Renamed: {pdf_file.name} -> {new_path.name}")
                stats["renamed"] += 1
            else:
                self._logger.info(f"Skipped: {pdf_file.name} ({reason})")
                stats["skipped"] += 1

        self._logger.info(
            f"Processing complete: {stats['renamed']} renamed, "
            f"{stats['skipped']} skipped"
        )

        return stats

    def _discover_files(self, directory: Path) -> list[Path]:
        """Discover PDF files in directory."""
        files: set[Path] = set()
        for pattern in ["*.pdf", "*.PDF"]:
            files.update(directory.glob(pattern))
        return sorted(files)


# =============================================================================
# Logging Configuration
# =============================================================================


def setup_logging(verbose: bool = False, log_file: Path | None = None) -> None:
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
    )


# =============================================================================
# CLI Interface
# =============================================================================


def parse_args() -> tuple[Path, ProcessingConfig]:
    """Parse command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Rename PDF files based on content analysis"
    )
    parser.add_argument("directory", type=Path, help="Directory containing PDF files")
    parser.add_argument(
        "-n",
        "--max-pages",
        type=int,
        default=3,
        help="Maximum number of pages to extract (default: 3)",
    )
    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Simulate renames without modifying files",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable detailed logging"
    )
    parser.add_argument(
        "--log-file", type=Path, help="Write log output to specified file"
    )

    args = parser.parse_args()

    config = ProcessingConfig(
        max_pages=args.max_pages,
        dry_run=args.dry_run,
        verbose=args.verbose,
        log_file=args.log_file,
    )

    return args.directory, config


# =============================================================================
# Main Entry Point
# =============================================================================


def main() -> None:
    """Main entry point for the PDF renaming tool."""
    if not _NLTK_AVAILABLE:
        print(
            "Error: NLTK is required. Install with: pip install nltk", file=sys.stderr
        )
        sys.exit(1)

    for resource in ["punkt", "stopwords", "averaged_perceptron_tagger"]:
        try:
            nltk.data.find(
                f"tokenizers/{resource}"
                if resource == "punkt"
                else f"corpora/{resource}"
            )
        except LookupError:
            nltk.download(resource)

    directory, config = parse_args()
    setup_logging(config.verbose, config.log_file)

    orchestrator = PdfRenamerOrchestrator(config)
    stats = orchestrator.run(directory)

    print(f"\nSummary:")
    print(f"  Total PDFs found: {stats['total']}")
    print(f"  Renamed:          {stats['renamed']}")
    print(f"  Skipped:          {stats['skipped']}")


if __name__ == "__main__":
    main()
