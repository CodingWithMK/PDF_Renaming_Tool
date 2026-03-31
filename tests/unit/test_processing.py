"""Unit tests for file renamer and pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.pdf_renamer.processing.renamer import FileRenamer, RenameResult
from src.pdf_renamer.processing.pipeline import PdfProcessor, ProcessingResult


class TestFileRenamer:
    """Tests for FileRenamer."""

    def test_basic_rename(self, tmp_path: Path) -> None:
        original = tmp_path / "old.pdf"
        original.write_text("content")

        renamer = FileRenamer()
        result = renamer.rename(original, "new_name", tmp_path)

        assert result.success is True
        assert (tmp_path / "new_name.pdf").exists()
        assert not original.exists()

    def test_rename_with_collision(self, tmp_path: Path) -> None:
        original = tmp_path / "old.pdf"
        original.write_text("new content")

        # Create existing file
        (tmp_path / "doc.pdf").write_text("existing")

        renamer = FileRenamer()
        result = renamer.rename(original, "doc", tmp_path)

        assert result.success is True
        assert (tmp_path / "doc_1.pdf").exists()
        assert (tmp_path / "doc_1.pdf").read_text() == "new content"

    def test_rename_multiple_collisions(self, tmp_path: Path) -> None:
        original = tmp_path / "old.pdf"
        original.write_text("newest")

        # Create existing files
        (tmp_path / "doc.pdf").write_text("existing 1")
        (tmp_path / "doc_1.pdf").write_text("existing 2")

        renamer = FileRenamer()
        result = renamer.rename(original, "doc", tmp_path)

        assert result.success is True
        assert (tmp_path / "doc_2.pdf").exists()

    def test_dry_run_does_not_rename(self, tmp_path: Path) -> None:
        original = tmp_path / "old.pdf"
        original.write_text("content")

        renamer = FileRenamer(dry_run=True)
        result = renamer.rename(original, "new_name", tmp_path)

        assert result.success is True
        assert original.exists()  # File not actually renamed
        assert not (tmp_path / "new_name.pdf").exists()

    def test_rename_error_returns_failure(self, tmp_path: Path) -> None:
        original = tmp_path / "old.pdf"
        original.write_text("content")

        # Mock the rename to fail
        renamer = FileRenamer()
        with patch("os.rename", side_effect=OSError("Permission denied")):
            result = renamer.rename(original, "new_name", tmp_path)

        assert result.success is False
        assert result.error is not None
        assert "Permission denied" in result.error


class TestProcessingResult:
    """Tests for ProcessingResult dataclass."""

    def test_result_with_skip_reason(self) -> None:
        result = ProcessingResult(
            source_path=Path("/test.pdf"),
            reason="no text",
        )
        assert result.reason == "no text"
        assert result.new_name is None
        assert result.rename_result is None

    def test_result_with_success(self) -> None:
        rename_result = RenameResult(
            original_path=Path("/old.pdf"),
            new_path=Path("/new.pdf"),
            success=True,
        )
        result = ProcessingResult(
            source_path=Path("/old.pdf"),
            new_name="new",
            rename_result=rename_result,
        )
        assert result.new_name == "new"
        assert result.rename_result.success is True
        assert result.reason is None
