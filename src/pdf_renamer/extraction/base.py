"""Abstract base class for text extractors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.pdf_renamer.models import PdfDocument


class TextExtractor(ABC):
    """Extracts text from document files.

    This is the extension point for adding new document formats (OCR, etc.)
    without modifying existing code (Open/Closed Principle).
    """

    @abstractmethod
    def extract(self, path: Path, max_pages: int = 3) -> str:
        """Extract text from first max_pages pages.

        Args:
            path: Path to the document file.
            max_pages: Maximum number of pages to extract.

        Returns:
            Concatenated text from the extracted pages.
        """
        ...

    @abstractmethod
    def extract_document(self, path: Path, max_pages: int = 3) -> PdfDocument:
        """Extract a PDF document with cached page texts.

        This method opens the PDF once and returns a PdfDocument object
        with all page texts cached, avoiding duplicate reads.

        Args:
            path: Path to the PDF file.
            max_pages: Maximum number of pages to extract.

        Returns:
            PdfDocument with cached page texts.
        """
        ...

    @abstractmethod
    def supports(self, path: Path) -> bool:
        """Check if this extractor can handle the given file.

        Args:
            path: Path to the document file.

        Returns:
            True if this extractor can process the file.
        """
        ...
