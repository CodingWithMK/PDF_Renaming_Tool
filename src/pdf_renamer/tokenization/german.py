"""German tokenizer using NLTK with compound-word awareness."""

from __future__ import annotations

import logging
from collections import Counter

from nltk import word_tokenize  # type: ignore[import-untyped]
from nltk.corpus import stopwords  # type: ignore[import-untyped]

from src.pdf_renamer.tokenization.base import Tokenizer
from src.pdf_renamer.tokenization.stopwords import CUSTOM_STOPWORDS_DE

logger = logging.getLogger(__name__)


class GermanTokenizer(Tokenizer):
    """German tokenizer that filters stopwords and handles compound words.

    German compound words (Komposita) are preserved as single tokens,
    which is beneficial for filename uniqueness.

    Umlauts (ä, ö, ü, ß) are preserved by default.
    """

    def __init__(self, custom_stopwords: set[str] | None = None) -> None:
        """Initialize with optional custom stopwords.

        Args:
            custom_stopwords: Additional stopwords to filter. Merged with defaults.
        """
        self._stopwords: set[str] = set()
        try:
            self._stopwords = set(stopwords.words("german"))
        except LookupError:
            logger.warning("NLTK 'stopwords' not downloaded; using custom only")
        self._stopwords = (
            self._stopwords | CUSTOM_STOPWORDS_DE | (custom_stopwords or set())
        )

    def tokenize(self, text: str) -> list[str]:
        """Tokenize German text and filter stopwords.

        Args:
            text: Raw German text.

        Returns:
            Filtered list of tokens.
        """
        normalized = self._normalize_text(text)
        tokens = word_tokenize(normalized)
        return self._filter_tokens(tokens, self._stopwords)

    def get_top_words(self, text: str, n: int = 4) -> list[str]:
        """Extract top N words from German text by frequency.

        German nouns are always capitalized, but we normalize to lowercase
        for consistent frequency counting.

        Args:
            text: Raw German text.
            n: Number of top words to return.

        Returns:
            List of top N words by frequency.
        """
        tokens = self.tokenize(text)
        if not tokens:
            return []
        counter = Counter(tokens)
        return [word for word, _ in counter.most_common(n)]
