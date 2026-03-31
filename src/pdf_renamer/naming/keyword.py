"""Keyword-based naming strategy."""

from __future__ import annotations

from src.pdf_renamer.naming.base import NamingResult, NamingStrategy, ProcessingContext
from src.pdf_renamer.naming.slugifier import Slugifier
from src.pdf_renamer.tokenization.registry import TokenizerRegistry


class KeywordNamingStrategy(NamingStrategy):
    """Generates filenames from extracted keywords.

    Used as a fallback when no title can be extracted.
    Extracts top keywords based on the detected language.
    """

    def __init__(
        self,
        registry: TokenizerRegistry,
        slugifier: Slugifier | None = None,
        num_keywords: int = 1,
    ) -> None:
        """Initialize with tokenizer registry.

        Args:
            registry: TokenizerRegistry with registered language tokenizers.
            slugifier: Slugifier instance. Creates default if None.
            num_keywords: Number of top keywords to use for naming.
        """
        self._registry = registry
        self._slugifier = slugifier or Slugifier()
        self._num_keywords = num_keywords

    def can_handle(self, context: ProcessingContext) -> bool:
        """Check if tokenization is available for the detected language.

        Args:
            context: Processing context.

        Returns:
            True if a tokenizer is available for the language.
        """
        return self._registry.get(context.language) is not None

    def generate(self, context: ProcessingContext) -> NamingResult | None:
        """Generate a filename from top keywords.

        Args:
            context: Processing context with extracted text.

        Returns:
            NamingResult with top keyword, or None if no keywords found.
        """
        tokenizer = self._registry.get(context.language)
        if tokenizer is None:
            return None

        tokens = tokenizer.tokenize(context.text)
        if not tokens:
            return None

        # Sort by length (descending) then alphabetically for determinism
        # Longer words are typically more distinctive
        sorted_tokens = sorted(tokens, key=lambda w: (-len(w), w))
        top_words = sorted_tokens[: self._num_keywords]

        if not top_words:
            return None

        # Use the most distinctive (longest) word
        keyword = top_words[0]
        slug = self._slugifier.sanitize(keyword, context.language)

        return NamingResult(name=slug, strategy_used="keyword")
