"""Data models for the PDF Renaming Tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RenamerConfig:
    """Configuration for the PDF renaming process.

    Attributes:
        directory: Path to the directory containing PDFs.
        max_pages: Maximum number of pages to extract text from.
        dry_run: If True, simulate renames without modifying files.
        verbose: If True, enable detailed logging output.
        log_file: Optional path to write log output to.
    """

    directory: Path
    max_pages: int = 3
    dry_run: bool = False
    verbose: bool = False
    log_file: Path | None = None


@dataclass
class PdfDocument:
    """Cached representation of a PDF document.

    Opens the PDF once and caches page texts to avoid duplicate reads
    when both text extraction and title extraction are needed.

    Attributes:
        path: Path to the PDF file.
        num_pages: Total number of pages in the document.
        pages: Extracted text for each cached page.
    """

    path: Path
    num_pages: int
    pages: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, path: Path, max_pages: int = 3) -> PdfDocument:
        """Load a PDF and cache text from the first max_pages pages.

        Args:
            path: Path to the PDF file.
            max_pages: Maximum number of pages to extract.

        Returns:
            A PdfDocument with cached page texts.

        Raises:
            FileNotFoundError: If the PDF file does not exist.
        """
        from PyPDF2 import PdfReader

        reader = PdfReader(str(path))
        total = len(reader.pages)
        num_to_read = min(total, max_pages)
        pages: list[str] = []
        for i in range(num_to_read):
            text = reader.pages[i].extract_text() or ""
            pages.append(text)
        return cls(path=path, num_pages=total, pages=pages)

    def all_text(self) -> str:
        """Return all cached page texts concatenated."""
        return "".join(self.pages)


@dataclass
class RenameResult:
    """Result of a file rename operation.

    Attributes:
        original_path: The original file path.
        new_path: The new file path after renaming.
        success: Whether the rename operation succeeded.
        error: Error message if the operation failed, None otherwise.
    """

    original_path: Path
    new_path: Path
    success: bool
    error: str | None = None
