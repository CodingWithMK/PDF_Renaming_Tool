"""Slugifier for converting text to filename-safe strings."""

from __future__ import annotations

import re


# Optional transliteration for German characters
GERMAN_TRANSLITERATION: dict[str, str] = {
    "ä": "ae",
    "ö": "oe",
    "ü": "ue",
    "ß": "ss",
    "Ä": "Ae",
    "Ö": "Oe",
    "Ü": "Ue",
}

# Characters that are invalid in filenames on most filesystems
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'


class Slugifier:
    """Converts text to filename-safe strings.

    By default, preserves international characters (Turkish, German).
    Can optionally transliterate German umlauts to ASCII.
    """

    def __init__(self, *, transliterate_german: bool = False) -> None:
        """Initialize the slugifier.

        Args:
            transliterate_german: If True, convert German umlauts to ASCII.
        """
        self._transliterate_german = transliterate_german

    def sanitize(self, text: str, lang: str = "en") -> str:
        """Make text safe for use as a filename.

        Args:
            text: The text to sanitize.
            lang: ISO 639-1 language code (used for transliteration rules).

        Returns:
            Filename-safe string.
        """
        text = text.strip().replace(" ", "_")

        # Remove invalid filename characters
        text = re.sub(INVALID_FILENAME_CHARS, "", text)

        # Optional German transliteration
        if self._transliterate_german and lang == "de":
            for src, tgt in GERMAN_TRANSLITERATION.items():
                text = text.replace(src, tgt)

        return text
