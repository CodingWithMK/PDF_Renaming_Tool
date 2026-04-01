"""Language detection implementations."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LanguageDetector(ABC):
    """Abstract base class for language detection.

    Allows swapping language detection backends without modifying
    business logic (Dependency Inversion Principle).
    """

    @abstractmethod
    def detect(self, text: str) -> str:
        """Detect the language of the given text.

        Args:
            text: The text to analyze.

        Returns:
            ISO 639-1 language code (e.g., 'en', 'de', 'tr').
        """
        ...


class LangdetectDetector(LanguageDetector):
    """Language detection using the langdetect library.

    Falls back to 'en' if detection fails (e.g., very short text).
    """

    def detect(self, text: str) -> str:
        """Detect language using langdetect.

        Args:
            text: The text to analyze.

        Returns:
            ISO 639-1 language code, defaults to 'en' on failure.
        """
        try:
            from langdetect import (
                detect as langdetect_detect,  # type: ignore[import-untyped]
            )

            result = langdetect_detect(text)
            # Validate result is a string (langdetect returns Any)
            if not isinstance(result, str):
                raise ValueError(f"Invalid language detection result: {result}")
            return result
        except Exception as e:
            logger.warning("Language detection failed: %s, defaulting to 'en'", e)
            return "en"
