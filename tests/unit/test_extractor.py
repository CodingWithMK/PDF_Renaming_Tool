"""Unit tests for text extractor."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pdf_renamer.extraction.pdf import PdfTextExtractor


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

    @patch("src.pdf_renamer.extraction.pdf.PdfReader")
    def test_extract_text(self, mock_reader_cls: MagicMock) -> None:
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Page 1 content"
        mock_reader.pages[1].extract_text.return_value = "Page 2 content"
        mock_reader.__len__ = lambda self: 2
        mock_reader_cls.return_value = mock_reader

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("test.pdf"), max_pages=2)

        assert "Page 1 content" in result
        assert "Page 2 content" in result

    @patch("src.pdf_renamer.extraction.pdf.PdfReader")
    def test_extract_respects_max_pages(self, mock_reader_cls: MagicMock) -> None:
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock() for _ in range(10)]
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i}"
        mock_reader.__len__ = lambda self: 10
        mock_reader_cls.return_value = mock_reader

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("test.pdf"), max_pages=2)

        assert "Page 0" in result
        assert "Page 1" in result
        assert "Page 2" not in result

    @patch("src.pdf_renamer.extraction.pdf.PdfReader")
    def test_extract_handles_none_text(self, mock_reader_cls: MagicMock) -> None:
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock()]
        mock_reader.pages[0].extract_text.return_value = None
        mock_reader.__len__ = lambda self: 1
        mock_reader_cls.return_value = mock_reader

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("test.pdf"), max_pages=1)

        assert result == ""

    @patch("src.pdf_renamer.extraction.pdf.PdfReader")
    def test_extract_handles_exception(self, mock_reader_cls: MagicMock) -> None:
        mock_reader_cls.side_effect = Exception("Corrupted PDF")

        extractor = PdfTextExtractor()
        result = extractor.extract(Path("corrupted.pdf"), max_pages=3)

        assert result == ""
