"""Unit tests for text extractor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.pdf_renamer.extraction.pdf import PdfTextExtractor
from src.pdf_renamer.models import PdfDocument


class TestPdfTextExtractor:
    """Tests for PdfTextExtractor."""

    def test_supports_pdf(self) -> None:
        extractor = PdfTextExtractor()
        assert extractor.supports(Path("document.pdf")) is True

    def test_supports_uppercase_pdf(self) -> None:
        extractor = PdfTextExtractor()
        assert extractor.supports(Path("document.PDF")) is True

    def test_does_not_support_txt(self) -> None:
        extractor = PdfTextExtractor()
        assert extractor.supports(Path("document.txt")) is False

    def test_does_not_support_docx(self) -> None:
        extractor = PdfTextExtractor()
        assert extractor.supports(Path("document.docx")) is False

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_extract_text(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that extract() returns concatenated page text."""
        mock_stat.return_value.st_size = 1024
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Page 1 content"
        mock_reader.pages[1].extract_text.return_value = "Page 2 content"
        mock_reader_cls.return_value = mock_reader

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("test.pdf"), max_pages=2)

        assert "Page 1 content" in result
        assert "Page 2 content" in result

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_extract_respects_max_pages(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that extract() only reads up to max_pages."""
        mock_stat.return_value.st_size = 1024
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock() for _ in range(10)]
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i}"
        mock_reader_cls.return_value = mock_reader

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("test.pdf"), max_pages=2)

        assert "Page 0" in result
        assert "Page 1" in result
        assert "Page 2" not in result

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_extract_handles_none_text(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that extract() handles pages that return None for text."""
        mock_stat.return_value.st_size = 1024
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock()]
        mock_reader.pages[0].extract_text.return_value = None
        mock_reader_cls.return_value = mock_reader

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("test.pdf"), max_pages=1)

        assert result == ""

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_extract_handles_exception(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that extract() returns empty string on error."""
        mock_stat.return_value.st_size = 1024
        mock_reader_cls.side_effect = Exception("Corrupted PDF")

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("corrupted.pdf"), max_pages=3)

        assert result == ""

    def test_extract_handles_missing_file(self) -> None:
        """Test that extract() returns empty string for non-existent file."""
        extractor = PdfTextExtractor()
        result = extractor.extract(Path("/nonexistent/file.pdf"), max_pages=3)
        assert result == ""

    @patch("pypdf.PdfReader")
    @patch.object(Path, "exists", return_value=True)
    @patch.object(Path, "stat")
    def test_extract_document_returns_pdf_document(
        self, mock_stat: MagicMock, mock_exists: MagicMock, mock_reader_cls: MagicMock
    ) -> None:
        """Test that extract_document() returns a PdfDocument instance."""
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
