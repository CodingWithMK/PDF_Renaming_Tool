"""Unit tests for the rename_pdf function."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from pdf_renamer import rename_pdf


class TestRenamePdf:
    """Tests for rename_pdf()."""

    def test_basic_rename(self, tmp_path: Path) -> None:
        """Test basic file renaming without collision."""
        original = tmp_path / "old.pdf"
        original.write_text("content")

        rename_pdf(str(original), "new_name", str(tmp_path))

        new_file = tmp_path / "new_name.pdf"
        assert new_file.exists()
        assert not original.exists()
        assert new_file.read_text() == "content"

    def test_rename_with_path_object(self, tmp_path: Path) -> None:
        """Test renaming using Path objects."""
        original = tmp_path / "old.pdf"
        original.write_text("content")

        rename_pdf(original, "new_name", tmp_path)

        new_file = tmp_path / "new_name.pdf"
        assert new_file.exists()

    def test_collision_handling_single(self, tmp_path: Path) -> None:
        """Test that collision creates _1 suffix."""
        original = tmp_path / "old.pdf"
        original.write_text("original")

        # Create existing file with target name
        existing = tmp_path / "doc.pdf"
        existing.write_text("existing")

        rename_pdf(str(original), "doc", str(tmp_path))

        # Should create doc_1.pdf
        renamed = tmp_path / "doc_1.pdf"
        assert renamed.exists()
        assert renamed.read_text() == "original"
        assert existing.exists()  # Original file unchanged

    def test_collision_handling_multiple(self, tmp_path: Path) -> None:
        """Test that multiple collisions increment suffix."""
        original = tmp_path / "old.pdf"
        original.write_text("new content")

        # Create existing files
        (tmp_path / "doc.pdf").write_text("existing 1")
        (tmp_path / "doc_1.pdf").write_text("existing 2")
        (tmp_path / "doc_2.pdf").write_text("existing 3")

        rename_pdf(str(original), "doc", str(tmp_path))

        # Should create doc_3.pdf
        renamed = tmp_path / "doc_3.pdf"
        assert renamed.exists()
        assert renamed.read_text() == "new content"

    def test_rename_preserves_content(self, tmp_path: Path) -> None:
        """Test that file content is preserved after rename."""
        original = tmp_path / "source.pdf"
        content = "Test PDF content with special chars: \u00e9\u00e8\u00ea"
        original.write_text(content)

        rename_pdf(str(original), "target", str(tmp_path))

        new_file = tmp_path / "target.pdf"
        assert new_file.read_text() == content

    def test_rename_adds_pdf_extension(self, tmp_path: Path) -> None:
        """Test that .pdf extension is always added."""
        original = tmp_path / "old.pdf"
        original.write_text("content")

        rename_pdf(str(original), "no_extension", str(tmp_path))

        new_file = tmp_path / "no_extension.pdf"
        assert new_file.exists()

    def test_rename_different_directory(self, tmp_path: Path) -> None:
        """Test renaming within a subdirectory."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        original = tmp_path / "old.pdf"
        original.write_text("content")

        rename_pdf(str(original), "new_name", str(subdir))

        new_file = subdir / "new_name.pdf"
        assert new_file.exists()
        assert not original.exists()
