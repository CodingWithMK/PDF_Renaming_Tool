"""PDF text extraction using PyPDF2."""

from __future__ import annotations

import logging
from pathlib import Path

from PyPDF2 import PdfReader

from src.pdf_renamer.extraction.base import TextExtractor

logger = logging.getLogger(__name__)


class PdfTextExtractor(TextExtractor):
    """Extracts text from PDF files using PyPDF2.

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
        text = ""
        try:
            reader = PdfReader(str(path))
            num_pages = min(len(reader.pages), max_pages)
            for i in range(num_pages):
                text += reader.pages[i].extract_text() or ""
        except Exception as e:
            logger.error("Error reading %s: %s", path, e)
        return text

    def supports(self, path: Path) -> bool:
        """Check if the file is a PDF.

        Args:
            path: Path to the document file.

        Returns:
            True if the file has a .pdf extension.
        """
        return path.suffix.lower() == ".pdf"
