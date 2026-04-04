"""
Unit tests for the refactored PDF Renaming Tool.

Tests cover:
- German stopwords and tokenization
- Path validation and security
- Resource limits
- Slugification with German umlauts
- Processing pipeline
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from pdf_renamer import (
    GermanStopwords,
    TurkishStopwords,
    EnglishStopwords,
    GERMAN_TRANSLITERATION,
    PathValidator,
    PathValidationError,
    ResourceLimiter,
    ResourceLimits,
    ResourceExhaustedError,
    PdfTextExtractor,
    LanguageDetector,
    TitleExtractor,
    EnglishTokenizer,
    GermanTokenizer,
    TurkishTokenizer,
    TokenizerRegistry,
    EnglishKeywordExtractor,
    GermanKeywordExtractor,
    TurkishKeywordExtractor,
    Slugifier,
    FileRenamer,
    PdfProcessingPipeline,
    ProcessingConfig,
    SupportedLanguage,
)


# =============================================================================
# Stopwords Tests
# =============================================================================


class TestGermanStopwords:
    """Tests for German stopwords."""

    def test_core_stopwords_not_empty(self):
        """German core stopwords should not be empty."""
        assert len(GermanStopwords.CORE) > 0

    def test_document_stopwords_not_empty(self):
        """German document stopwords should not be empty."""
        assert len(GermanStopwords.DOCUMENT) > 0

    def test_get_all_combines_both(self):
        """get_all should combine core and document stopwords."""
        all_words = GermanStopwords.get_all()
        assert GermanStopwords.CORE.issubset(all_words)
        assert GermanStopwords.DOCUMENT.issubset(all_words)

    def test_contains_common_articles(self):
        """Should contain common German articles."""
        all_words = GermanStopwords.get_all()
        assert "der" in all_words
        assert "die" in all_words
        assert "das" in all_words


class TestTurkishStopwords:
    """Tests for Turkish stopwords."""

    def test_core_stopwords_not_empty(self):
        """Turkish core stopwords should not be empty."""
        assert len(TurkishStopwords.CORE) > 0

    def test_get_all(self):
        """Should get all Turkish stopwords."""
        all_words = TurkishStopwords.get_all()
        assert "icin" in all_words
        assert "ve" in all_words


class TestEnglishStopwords:
    """Tests for English stopwords."""

    def test_document_stopwords_not_empty(self):
        """English document stopwords should not be empty."""
        assert len(EnglishStopwords.DOCUMENT) > 0


# =============================================================================
# Path Validation Tests
# =============================================================================


class TestPathValidator:
    """Tests for path validation security."""

    def test_validate_safe_path_allows_nested(self):
        """Should allow paths within base directory."""
        base = Path("/safe/directory")
        target = Path("/safe/directory/file.pdf")
        assert PathValidator.validate_safe_path(base, target) is True

    def test_validate_safe_path_rejects_traversal(self):
        """Should reject path traversal attempts."""
        base = Path("/safe/directory")
        target = Path("/unsafe/../../../etc/passwd")
        with pytest.raises(PathValidationError):
            PathValidator.validate_safe_path(base, target)

    def test_sanitize_filename_removes_dangerous_chars(self):
        """Should remove dangerous characters."""
        filename = 'file<>:"/\\|?*.pdf'
        sanitized = PathValidator.sanitize_filename(filename)
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert ":" not in sanitized

    def test_sanitize_filename_handles_windows_reserved(self):
        """Should handle Windows reserved names."""
        sanitized = PathValidator.sanitize_filename("CON.pdf")
        assert sanitized.startswith("_")

    def test_sanitize_filename_truncates_long_names(self):
        """Should truncate excessively long filenames."""
        long_name = "a" * 300 + ".pdf"
        sanitized = PathValidator.sanitize_filename(long_name)
        assert len(sanitized) <= 204


# =============================================================================
# Resource Limit Tests
# =============================================================================


class TestResourceLimiter:
    """Tests for resource limits."""

    def test_validate_file_size_under_limit(self, tmp_path):
        """Should allow files under size limit."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("x" * 1024)
        limiter = ResourceLimiter(ResourceLimits(max_file_size_mb=10))
        limiter.validate_file(test_file)

    def test_validate_file_size_exceeds_limit(self, tmp_path):
        """Should reject files exceeding size limit."""
        test_file = tmp_path / "test.pdf"
        test_file.write_text("x" * (11 * 1024 * 1024))
        limiter = ResourceLimiter(ResourceLimits(max_file_size_mb=10))
        with pytest.raises(ResourceExhaustedError):
            limiter.validate_file(test_file)

    def test_validate_text_under_limit(self):
        """Should allow text under length limit."""
        limiter = ResourceLimiter()
        limiter.validate_text("a" * 1000)

    def test_validate_text_exceeds_limit(self):
        """Should reject text exceeding length limit."""
        limiter = ResourceLimiter(ResourceLimits(max_text_length=100))
        with pytest.raises(ResourceExhaustedError):
            limiter.validate_text("a" * 200)


# =============================================================================
# Language Support Tests
# =============================================================================


class TestSupportedLanguage:
    """Tests for language enum."""

    def test_from_code_english(self):
        """Should convert 'en' to ENGLISH."""
        assert SupportedLanguage.from_code("en") == SupportedLanguage.ENGLISH

    def test_from_code_german(self):
        """Should convert 'de' to GERMAN."""
        assert SupportedLanguage.from_code("de") == SupportedLanguage.GERMAN

    def test_from_code_turkish(self):
        """Should convert 'tr' to TURKISH."""
        assert SupportedLanguage.from_code("tr") == SupportedLanguage.TURKISH

    def test_from_code_unknown_defaults_english(self):
        """Should default to English for unknown codes."""
        assert SupportedLanguage.from_code("xx") == SupportedLanguage.ENGLISH


# =============================================================================
# Transliteration Tests
# =============================================================================


class TestGermanTransliteration:
    """Tests for German character transliteration."""

    def test_umlaut_mappings_exist(self):
        """Should have mappings for all umlauts."""
        assert "ä" in GERMAN_TRANSLITERATION
        assert "ö" in GERMAN_TRANSLITERATION
        assert "ü" in GERMAN_TRANSLITERATION
        assert "ß" in GERMAN_TRANSLITERATION

    def test_umlaut_to_ascii(self):
        """Should map umlauts to ASCII equivalents."""
        assert GERMAN_TRANSLITERATION["ä"] == "ae"
        assert GERMAN_TRANSLITERATION["ö"] == "oe"
        assert GERMAN_TRANSLITERATION["ü"] == "ue"
        assert GERMAN_TRANSLITERATION["ß"] == "ss"


# =============================================================================
# Tokenizer Tests
# =============================================================================


class TestGermanTokenizer:
    """Tests for German tokenizer."""

    @patch("pdf_renamer.word_tokenize")
    @patch("pdf_renamer.stopwords")
    def test_filters_german_stopwords(self, mock_stopwords, mock_tokenize):
        """Should filter German stopwords."""
        mock_stopwords.words.return_value = set()
        mock_tokenize.return_value = ["der", "test", "ist", "wichtig"]

        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("Der Test ist wichtig.")

        assert "der" not in result
        assert "ist" not in result

    @patch("pdf_renamer.word_tokenize")
    @patch("pdf_renamer.stopwords")
    def test_preserves_umlauts(self, mock_stopwords, mock_tokenize):
        """Should preserve German umlauts in tokens."""
        mock_stopwords.words.return_value = set()
        mock_tokenize.return_value = ["ärzte", "prüfen"]

        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("Ärzte prüfen.")

        assert "ärzte" in result
        assert "prüfen" in result


class TestEnglishTokenizer:
    """Tests for English tokenizer."""

    @patch("pdf_renamer.word_tokenize")
    @patch("pdf_renamer.stopwords")
    def test_filters_english_stopwords(self, mock_stopwords, mock_tokenize):
        """Should filter English stopwords."""
        mock_stopwords.words.return_value = {"the", "is"}
        mock_tokenize.return_value = ["the", "test", "is", "important"]

        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("The test is important.")

        assert "the" not in result
        assert "is" not in result
        assert "test" in result


# =============================================================================
# Tokenizer Registry Tests
# =============================================================================


class TestTokenizerRegistry:
    """Tests for tokenizer registry."""

    def test_register_and_get(self):
        """Should register and retrieve tokenizers."""
        registry = TokenizerRegistry()
        tokenizer = GermanTokenizer()
        registry.register(SupportedLanguage.GERMAN, tokenizer)
        assert registry.get(SupportedLanguage.GERMAN) is tokenizer

    def test_get_unknown_defaults_english(self):
        """Should default to English for unknown languages."""
        registry = TokenizerRegistry()
        en_tokenizer = EnglishTokenizer()
        registry.register(SupportedLanguage.ENGLISH, en_tokenizer)
        result = registry.get(SupportedLanguage.TURKISH)
        assert result is en_tokenizer


# =============================================================================
# Keyword Extractor Tests
# =============================================================================


class TestGermanKeywordExtractor:
    """Tests for German keyword extraction."""

    def test_extract_returns_top_words(self):
        """Should return top N words by frequency."""
        extractor = GermanKeywordExtractor()
        words = ["test", "test", "wichtig", "daten", "daten", "daten"]
        result = extractor.extract(words, n=2)
        assert "daten" in result
        assert len(result) <= 2

    def test_extract_empty_input(self):
        """Should handle empty input."""
        extractor = GermanKeywordExtractor()
        result = extractor.extract([], n=4)
        assert result == []


# =============================================================================
# Slugifier Tests
# =============================================================================


class TestSlugifier:
    """Tests for slugification."""

    def test_basic_slugify(self):
        """Should convert text to slug format."""
        slugifier = Slugifier()
        result = slugifier.slugify("Hello World", SupportedLanguage.ENGLISH)
        assert result == "Hello_World"

    def test_removes_special_chars(self):
        """Should remove special characters."""
        slugifier = Slugifier()
        result = slugifier.slugify("Test<>File", SupportedLanguage.ENGLISH)
        assert "<" not in result
        assert ">" not in result

    def test_transliterate_german_umlauts(self):
        """Should always transliterate German umlauts."""
        slugifier = Slugifier()
        result = slugifier.slugify("Ärger", SupportedLanguage.GERMAN)
        assert "ae" in result.lower()
        assert "ä" not in result

    def test_german_umlauts_always_transliterated(self):
        """German umlauts should always be transliterated for filesystem compatibility."""
        slugifier = Slugifier()
        result = slugifier.slugify("Ärger", SupportedLanguage.GERMAN)
        assert "Ae" in result
        assert "ä" not in result


# =============================================================================
# File Renamer Tests
# =============================================================================


class TestFileRenamer:
    """Tests for file renaming."""

    def test_rename_basic(self, tmp_path):
        """Should rename file successfully."""
        original = tmp_path / "test.pdf"
        original.write_text("test content")

        renamer = FileRenamer(dry_run=False)
        new_path, success = renamer.rename(original, "New_Name", tmp_path)

        assert success is True
        assert new_path.exists()
        assert new_path.name == "New_Name.pdf"

    def test_rename_collision_handling(self, tmp_path):
        """Should handle filename collisions."""
        existing = tmp_path / "test.pdf"
        existing.write_text("existing")

        original = tmp_path / "test.pdf"
        original.write_text("original")

        renamer = FileRenamer(dry_run=False)
        new_path, success = renamer.rename(original, "test", tmp_path)

        assert success is True
        assert new_path.name == "test_1.pdf"

    def test_dry_run_no_rename(self, tmp_path):
        """Should not rename in dry-run mode."""
        original = tmp_path / "test.pdf"
        original.write_text("test content")

        renamer = FileRenamer(dry_run=True)
        new_path, success = renamer.rename(original, "New_Name", tmp_path)

        assert success is True
        assert not (tmp_path / "New_Name.pdf").exists()


# =============================================================================
# Title Extractor Tests
# =============================================================================


class TestTitleExtractor:
    """Tests for title extraction."""

    def test_extract_from_valid_pages(self):
        """Should extract title from valid pages."""
        extractor = TitleExtractor()
        pages = [
            "This is the first page\nwith some content",
            "Chapter 1\nIntroduction to Machine Learning",
        ]
        result = extractor.extract(pages)
        assert result is not None

    def test_extract_empty_pages(self):
        """Should return None for empty pages."""
        extractor = TitleExtractor()
        result = extractor.extract([])
        assert result is None

    def test_prefers_non_all_caps(self):
        """Should prefer non-all-caps lines."""
        extractor = TitleExtractor()
        pages = [
            "CHAPTER TITLE (ALL CAPS)\nSome content here",
            "Introduction to Machine Learning\nwith examples",
        ]
        result = extractor.extract(pages)
        assert result and not result.isupper()


# =============================================================================
# Pipeline Integration Tests
# =============================================================================


class TestPdfProcessingPipeline:
    """Tests for the processing pipeline."""

    def test_pipeline_initialization(self):
        """Should initialize pipeline with config."""
        config = ProcessingConfig(max_pages=3)
        pipeline = PdfProcessingPipeline(config)
        assert pipeline is not None

    @patch("pdf_renamer.PdfTextExtractor")
    @patch("pdf_renamer.LanguageDetector")
    def test_process_empty_pdf(self, mock_detector, mock_extractor):
        """Should handle empty PDF gracefully."""
        config = ProcessingConfig(max_pages=3)
        pipeline = PdfProcessingPipeline(config)

        mock_extractor_instance = MagicMock()
        mock_extractor_instance.extract_pages.return_value = [""]
        mock_extractor.return_value = mock_extractor_instance

        result = pipeline.process(Path("test.pdf"))
        assert result[0] is None


# =============================================================================
# Configuration Tests
# =============================================================================


class TestProcessingConfig:
    """Tests for processing configuration."""

    def test_default_values(self):
        """Should have sensible defaults."""
        config = ProcessingConfig()
        assert config.max_pages == 3
        assert config.dry_run is False
        assert config.verbose is False

    def test_custom_values(self):
        """Should accept custom values."""
        config = ProcessingConfig(max_pages=10, dry_run=True, verbose=True)
        assert config.max_pages == 10
        assert config.dry_run is True
        assert config.verbose is True


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
