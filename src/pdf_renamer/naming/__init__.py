"""Naming strategies for generating filenames from PDF content."""

from src.pdf_renamer.naming.base import NamingResult, NamingStrategy
from src.pdf_renamer.naming.keyword import KeywordNamingStrategy
from src.pdf_renamer.naming.slugifier import Slugifier
from src.pdf_renamer.naming.title import TitleNamingStrategy

__all__ = [
    "NamingStrategy",
    "NamingResult",
    "Slugifier",
    "TitleNamingStrategy",
    "KeywordNamingStrategy",
]
