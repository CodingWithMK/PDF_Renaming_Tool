"""Naming strategies for generating filenames from PDF content."""

from src.pdf_renamer.naming.base import NamingStrategy, NamingResult
from src.pdf_renamer.naming.slugifier import Slugifier
from src.pdf_renamer.naming.title import TitleNamingStrategy
from src.pdf_renamer.naming.keyword import KeywordNamingStrategy

__all__ = [
    "NamingStrategy",
    "NamingResult",
    "Slugifier",
    "TitleNamingStrategy",
    "KeywordNamingStrategy",
]
