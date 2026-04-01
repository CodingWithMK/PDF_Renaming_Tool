"""Tests to validate the fixes from FIX_PLAN.md."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pdf_renamer.extraction.pdf import PdfTextExtractor
from src.pdf_renamer.language.detector import LangdetectDetector
from src.pdf_renamer.models import PdfDocument
from src.pdf_renamer.naming.base import ProcessingContext
from src.pdf_renamer.naming.title import TitleNamingStrategy


class TestPhase1TypeMismatchFix:
    """Tests for Phase 1: Type mismatch bug fix in title.py."""

    def test_generate_with_none_title_returns_none(self) -> None:
        """Test that generate() returns None when title_candidate is None."""
        strategy = TitleNamingStrategy()
        context = ProcessingContext(
            text="some text",
            language="en",
            title_candidate=None,
        )
        # can_handle() should return False
        assert strategy.can_handle(context) is False
        # generate() should return None
        result = strategy.generate(context)
        assert result is None

    def test_generate_with_valid_title_succeeds(self) -> None:
        """Test that generate() works with valid title."""
        strategy = TitleNamingStrategy()
        context = ProcessingContext(
            text="some text",
            language="en",
            title_candidate="A Valid Document Title",
        )
        # can_handle() should return True
        assert strategy.can_handle(context) is True
        # generate() should succeed
        result = strategy.generate(context)
        assert result is not None
        assert result.strategy_used == "title"

    def test_can_handle_returns_false_then_generate_is_safe(self) -> None:
        """Test that when can_handle() returns False, generate() is safe."""
        strategy = TitleNamingStrategy()
        # Short title - can_handle returns False
        context = ProcessingContext(
            text="text",
            language="en",
            title_candidate="Hi",
        )
        assert strategy.can_handle(context) is False
        assert strategy.generate(context) is None


class TestPhase2PypdfMigration:
    """Tests for Phase 2: PyPDF2 to pypdf migration."""

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_extractor_uses_pypdf(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that PdfTextExtractor uses pypdf, not PyPDF2."""
        mock_stat.return_value.st_size = 1024
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Test content"
        mock_reader_cls.return_value = mock_reader

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("test.pdf"), max_pages=1)

        # If pypdf is being used, the mock should be called
        mock_reader_cls.assert_called_once()
        assert "Test content" in result

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_pdf_document_uses_pypdf(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that PdfDocument.load() uses pypdf, not PyPDF2."""
        mock_stat.return_value.st_size = 1024
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Test content"
        mock_reader_cls.return_value = mock_reader

        doc = PdfDocument.load(Path("test.pdf"), max_pages=1)

        mock_reader_cls.assert_called_once()
        assert doc.pages == ["Test content"]


class TestPhase5DuplicatePdfReadsFix:
    """Tests for Phase 5: Eliminate duplicate PDF reads."""

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_extract_uses_extract_document(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that extract() uses extract_document() internally."""
        mock_stat.return_value.st_size = 1024
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Page 1"
        mock_reader.pages[1].extract_text.return_value = "Page 2"
        mock_reader_cls.return_value = mock_reader

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("test.pdf"), max_pages=2)

        # PDF should only be read once
        assert mock_reader_cls.call_count == 1
        assert "Page 1" in result
        assert "Page 2" in result

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_extract_document_caches_pages(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that extract_document() returns a PdfDocument with cached pages."""
        mock_stat.return_value.st_size = 1024
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Page 1"
        mock_reader.pages[1].extract_text.return_value = "Page 2"
        mock_reader_cls.return_value = mock_reader

        extractor = PdfTextExtractor()
        doc = extractor.extract_document(Path("test.pdf"), max_pages=2)

        assert isinstance(doc, PdfDocument)
        assert doc.pages == ["Page 1", "Page 2"]
        assert doc.all_text() == "Page 1Page 2"


class TestPhase6LanguageDetectionFix:
    """Tests for Phase 6: Improve language detection return type."""

    @patch("langdetect.detect")
    def test_detect_validates_string_result(self, mock_detect: MagicMock) -> None:
        """Test that detect() validates the result is a string."""
        mock_detect.return_value = "en"
        detector = LangdetectDetector()
        result = detector.detect("This is English text")
        assert result == "en"
        assert isinstance(result, str)

    @patch("langdetect.detect")
    def test_detect_handles_non_string_result(self, mock_detect: MagicMock) -> None:
        """Test that detect() handles non-string results gracefully."""
        # Simulate langdetect returning an unexpected type
        mock_detect.return_value = 123  # Invalid type
        detector = LangdetectDetector()
        result = detector.detect("Some text")
        # Should fall back to "en"
        assert result == "en"

    @patch("langdetect.detect")
    def test_detect_handles_exception(self, mock_detect: MagicMock) -> None:
        """Test that detect() handles exceptions gracefully."""
        mock_detect.side_effect = Exception("Detection failed")
        detector = LangdetectDetector()
        result = detector.detect("Some text")
        assert result == "en"


class TestPhase7ErrorHandlingFix:
    """Tests for Phase 7: Enhance error handling in extraction."""

    def test_pdf_document_raises_on_missing_file(self) -> None:
        """Test that PdfDocument.load() raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            PdfDocument.load(Path("/nonexistent/path/to/file.pdf"))

    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_pdf_document_raises_on_empty_file(
        self, mock_stat: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test that PdfDocument.load() raises ValueError for empty file."""
        mock_stat.return_value.st_size = 0
        with pytest.raises(ValueError, match="empty"):
            PdfDocument.load(Path("/path/to/empty.pdf"))

    def test_extractor_handles_missing_file_gracefully(self) -> None:
        """Test that extract() returns empty string for missing file."""
        extractor = PdfTextExtractor()
        result = extractor.extract(Path("/nonexistent/file.pdf"))
        assert result == ""

    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_extractor_handles_empty_file_gracefully(
        self, mock_stat: MagicMock, mock_exists: MagicMock
    ) -> None:
        """Test that PdfTextExtractor.extract() returns empty string for empty file."""
        mock_stat.return_value.st_size = 0
        extractor = PdfTextExtractor()
        result = extractor.extract(Path("/path/to/empty.pdf"))
        assert result == ""

    def test_extractor_extract_document_returns_empty_doc_on_error(self) -> None:
        """Test that extract_document() returns empty PdfDocument on error."""
        extractor = PdfTextExtractor()
        doc = extractor.extract_document(Path("/nonexistent/file.pdf"))
        assert doc.pages == []
        assert doc.num_pages == 0
        assert doc.all_text() == ""


class TestIntegrationPipelineWithCaching:
    """Integration tests for the pipeline with PdfDocument caching."""

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_pdf_read_only_once_during_processing(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that PDF is only read once during full processing pipeline."""
        mock_stat.return_value.st_size = 1024
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock()]
        mock_reader.pages[0].extract_text.return_value = (
            "Introduction to Machine Learning\n\n"
            "This paper discusses the fundamentals of machine learning..."
        )
        mock_reader_cls.return_value = mock_reader

        # Simulate what the pipeline does
        extractor = PdfTextExtractor()
        doc = extractor.extract_document(Path("test.pdf"), max_pages=3)

        # Get text from cached document
        text = doc.all_text()

        # Extract title candidate from cached pages
        lines = []
        for page_text in doc.pages:
            if page_text:
                page_lines = page_text.split("\n")
                filtered = [
                    line.strip() for line in page_lines if len(line.strip()) >= 6
                ]
                lines.extend(filtered)

        # PDF should only be read once
        assert mock_reader_cls.call_count == 1
        assert "Machine Learning" in text
        assert len(lines) > 0
