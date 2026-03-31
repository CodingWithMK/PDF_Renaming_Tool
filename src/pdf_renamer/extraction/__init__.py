"""Text extraction module for PDF documents."""

from src.pdf_renamer.extraction.base import TextExtractor
from src.pdf_renamer.extraction.pdf import PdfTextExtractor

__all__ = ["TextExtractor", "PdfTextExtractor"]
