"""Unit tests for the models module."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pdf_renamer.models import PdfDocument, RenameResult, RenamerConfig


class TestRenamerConfig:
    """Tests for RenamerConfig dataclass."""

    def test_default_values(self) -> None:
        config = RenamerConfig(directory=Path("/test"))
        assert config.directory == Path("/test")
        assert config.max_pages == 3
        assert config.dry_run is False
        assert config.verbose is False
        assert config.log_file is None

    def test_custom_values(self) -> None:
        config = RenamerConfig(
            directory=Path("/custom"),
            max_pages=5,
            dry_run=True,
            verbose=True,
            log_file=Path("/log.txt"),
        )
        assert config.max_pages == 5
        assert config.dry_run is True
        assert config.verbose is True
        assert config.log_file == Path("/log.txt")

    def test_frozen(self) -> None:
        config = RenamerConfig(directory=Path("/test"))
        with pytest.raises(AttributeError):
            config.max_pages = 10  # type: ignore[misc]


class TestRenameResult:
    """Tests for RenameResult dataclass."""

    def test_success_result(self) -> None:
        result = RenameResult(
            original_path=Path("/old.pdf"),
            new_path=Path("/new.pdf"),
            success=True,
        )
        assert result.success is True
        assert result.error is None

    def test_failure_result(self) -> None:
        result = RenameResult(
            original_path=Path("/old.pdf"),
            new_path=Path("/new.pdf"),
            success=False,
            error="Permission denied",
        )
        assert result.success is False
        assert result.error == "Permission denied"


class TestPdfDocument:
    """Tests for PdfDocument dataclass."""

    def test_all_text_concatenates_pages(self) -> None:
        doc = PdfDocument(
            path=Path("/test.pdf"),
            num_pages=3,
            pages=["Hello ", "Beautiful ", "World"],
        )
        assert doc.all_text() == "Hello Beautiful World"

    def test_all_text_empty_pages(self) -> None:
        doc = PdfDocument(path=Path("/test.pdf"), num_pages=0, pages=[])
        assert doc.all_text() == ""

    @patch("PyPDF2.PdfReader")
    def test_load_extracts_pages(self, mock_reader_cls: MagicMock) -> None:
        """Test that load() opens PDF and extracts text from pages."""
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock(), MagicMock()]
        mock_reader.pages[0].extract_text.return_value = "Page 1"
        mock_reader.pages[1].extract_text.return_value = "Page 2"
        mock_reader.pages[2].extract_text.return_value = "Page 3"
        mock_reader_cls.return_value = mock_reader

        doc = PdfDocument.load(Path("/test.pdf"), max_pages=3)

        assert doc.num_pages == 3
        assert doc.pages == ["Page 1", "Page 2", "Page 3"]
        assert doc.path == Path("/test.pdf")

    @patch("PyPDF2.PdfReader")
    def test_load_respects_max_pages(self, mock_reader_cls: MagicMock) -> None:
        """Test that load() respects max_pages limit."""
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock() for _ in range(10)]
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i}"
        mock_reader_cls.return_value = mock_reader

        doc = PdfDocument.load(Path("/test.pdf"), max_pages=2)

        assert doc.num_pages == 10  # Total pages unchanged
        assert len(doc.pages) == 2  # Only 2 extracted
        assert doc.pages == ["Page 0", "Page 1"]

    @patch("PyPDF2.PdfReader")
    def test_load_handles_none_text(self, mock_reader_cls: MagicMock) -> None:
        """Test that load() handles pages that return None for text."""
        mock_reader = MagicMock()
        mock_reader.pages = [MagicMock(), MagicMock()]
        mock_reader.pages[0].extract_text.return_value = None
        mock_reader.pages[1].extract_text.return_value = "Real text"
        mock_reader_cls.return_value = mock_reader

        doc = PdfDocument.load(Path("/test.pdf"), max_pages=2)

        assert doc.pages == ["", "Real text"]
