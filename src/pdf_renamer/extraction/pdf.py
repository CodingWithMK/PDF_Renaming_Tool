"""PDF text extraction using pypdf."""

from __future__ import annotations

import logging
from pathlib import Path

from src.pdf_renamer.extraction.base import TextExtractor
from src.pdf_renamer.models import PdfDocument

logger = logging.getLogger(__name__)


class PdfTextExtractor(TextExtractor):
    """Extracts text from PDF files using pypdf.

    Supports extracting text from a specified number of pages
    starting from the first page.
    """

    def extract(self, path: Path, max_pages: int = 3) -> str:
        """Extract text from first max_pages pages of a PDF.

        Args:
            path: Path to the PDF file.
            max_pages: Maximum number of pages to extract.

        Returns:
            Concatenated text from the extracted pages.
        """
        doc = self.extract_document(path, max_pages)
        return doc.all_text()

    def extract_document(self, path: Path, max_pages: int = 3) -> PdfDocument:
        """Extract a PDF document with cached page texts.

        Opens the PDF once and returns a PdfDocument object with all page
        texts cached, avoiding duplicate reads.

        Args:
            path: Path to the PDF file.
            max_pages: Maximum number of pages to extract.

        Returns:
            PdfDocument with cached page texts.
        """
        try:
            return PdfDocument.load(path, max_pages)
        except Exception as e:
            logger.error("Error reading %s: %s", path, e)
            # Return empty document on error
            return PdfDocument(path=path, num_pages=0, pages=[])

    def supports(self, path: Path) -> bool:
        """Check if the file is a PDF.

        Args:
            path: Path to the document file.

        Returns:
            True if the file has a .pdf extension.
        """
        return path.suffix.lower() == ".pdf"
