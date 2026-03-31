"""Tokenizer registry for dynamic language-to-tokenizer mapping."""

from __future__ import annotations

import logging

from src.pdf_renamer.tokenization.base import Tokenizer

logger = logging.getLogger(__name__)


class TokenizerRegistry:
    """Maps language codes to Tokenizer implementations.

    Allows adding new languages without modifying existing code (OCP).
    """

    def __init__(self) -> None:
        self._tokenizers: dict[str, Tokenizer] = {}

    def register(self, lang: str, tokenizer: Tokenizer) -> None:
        """Register a tokenizer for a language code.

        Args:
            lang: ISO 639-1 language code (e.g., 'en', 'de', 'tr').
            tokenizer: Tokenizer instance for this language.
        """
        self._tokenizers[lang] = tokenizer
        logger.debug("Registered tokenizer for language: %s", lang)

    def get(self, lang: str) -> Tokenizer | None:
        """Get the tokenizer for a language code.

        Args:
            lang: ISO 639-1 language code.

        Returns:
            Tokenizer instance or None if not registered.
        """
        return self._tokenizers.get(lang)

    def get_or_default(self, lang: str) -> Tokenizer:
        """Get the tokenizer for a language, falling back to English.

        Args:
            lang: ISO 639-1 language code.

        Returns:
            Tokenizer for the language, or English tokenizer as fallback.
        """
        tokenizer = self._tokenizers.get(lang)
        if tokenizer is not None:
            return tokenizer

        # Try English as fallback
        default = self._tokenizers.get("en")
        if default is not None:
            logger.warning("No tokenizer for '%s', using English fallback", lang)
            return default

        # Should not happen if properly initialized
        raise ValueError(
            f"No tokenizer available for '{lang}' and no English fallback registered"
        )

    @property
    def supported_languages(self) -> list[str]:
        """Return list of registered language codes."""
        return list(self._tokenizers.keys())
