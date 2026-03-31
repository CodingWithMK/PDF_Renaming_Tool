"""Shared test fixtures for PDF Renaming Tool tests."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_dir(tmp_path: Path) -> Path:
    """Provide a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    """Create a minimal PDF-like file for testing (mock, not a real PDF)."""
    pdf_path = tmp_path / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4 mock content")
    return pdf_path
