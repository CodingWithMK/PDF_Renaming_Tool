"""Abstract base class for text tokenizers."""

from __future__ import annotations

import re
import string
from abc import ABC, abstractmethod

from nltk import word_tokenize


class Tokenizer(ABC):
    """Abstract tokenizer for language-specific text processing.

    Open for extension (new languages) without modification (OCP).
    """

    @abstractmethod
    def tokenize(self, text: str) -> list[str]:
        """Tokenize text and return filtered words.

        Args:
            text: Raw text to tokenize.

        Returns:
            List of filtered tokens (lowercase, no stopwords).
        """
        ...

    def _normalize_text(self, text: str) -> str:
        """Lowercase and replace punctuation with spaces.

        Args:
            text: Raw text to normalize.

        Returns:
            Normalized text.
        """
        text = text.lower()
        text = re.sub(f"[{re.escape(string.punctuation)}]", " ", text)
        return text

    def _filter_tokens(
        self, tokens: list[str], stopwords: set[str], min_length: int = 4
    ) -> list[str]:
        """Filter tokens: alphabetic only, not stopwords, minimum length.

        Args:
            tokens: List of raw tokens.
            stopwords: Set of stopwords to exclude.
            min_length: Minimum token length to keep.

        Returns:
            Filtered list of tokens.
        """
        return [
            t
            for t in tokens
            if t.isalpha() and t not in stopwords and len(t) >= min_length
        ]
