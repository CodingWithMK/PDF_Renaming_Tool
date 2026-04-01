"""English tokenizer using NLTK with POS tagging for noun extraction."""

from __future__ import annotations

import logging
from collections import Counter

from nltk import pos_tag, word_tokenize  # type: ignore[import-untyped]
from nltk.corpus import stopwords  # type: ignore[import-untyped]

from src.pdf_renamer.tokenization.base import Tokenizer
from src.pdf_renamer.tokenization.stopwords import CUSTOM_STOPWORDS_EN

logger = logging.getLogger(__name__)


class EnglishTokenizer(Tokenizer):
    """English tokenizer that filters stopwords and can extract top nouns.

    Uses NLTK for tokenization and POS tagging.
    """

    def __init__(self, custom_stopwords: set[str] | None = None) -> None:
        """Initialize with optional custom stopwords.

        Args:
            custom_stopwords: Additional stopwords to filter. Merged with defaults.
        """
        self._stopwords: set[str] = set()
        try:
            self._stopwords = set(stopwords.words("english"))
        except LookupError:
            logger.warning("NLTK 'stopwords' not downloaded; using custom only")
        self._stopwords = (
            self._stopwords | CUSTOM_STOPWORDS_EN | (custom_stopwords or set())
        )

    def tokenize(self, text: str) -> list[str]:
        """Tokenize English text and filter stopwords.

        Args:
            text: Raw English text.

        Returns:
            Filtered list of tokens.
        """
        normalized = self._normalize_text(text)
        tokens = word_tokenize(normalized)
        return self._filter_tokens(tokens, self._stopwords)

    def get_top_nouns(self, text: str, n: int = 4) -> list[str]:
        """Extract top N nouns from English text using POS tagging.

        Args:
            text: Raw English text.
            n: Number of top nouns to return.

        Returns:
            List of top N nouns by frequency.
        """
        tokens = self.tokenize(text)
        if not tokens:
            return []
        tagged = pos_tag(tokens)
        nouns = [word for word, pos in tagged if pos.startswith("NN")]
        counter = Counter(nouns)
        return [word for word, _ in counter.most_common(n)]
