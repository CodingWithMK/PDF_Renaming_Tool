"""Unit tests for tokenizers (English, Turkish, German)."""

from __future__ import annotations

import pytest

from src.pdf_renamer.tokenization.english import EnglishTokenizer
from src.pdf_renamer.tokenization.turkish import TurkishTokenizer
from src.pdf_renamer.tokenization.german import GermanTokenizer
from src.pdf_renamer.tokenization.registry import TokenizerRegistry


class TestEnglishTokenizer:
    """Tests for EnglishTokenizer."""

    def test_tokenize_basic(self) -> None:
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("The quick brown fox jumps over the lazy dog")
        assert "quick" in result
        assert "brown" in result
        assert "jumps" in result

    def test_tokenize_filters_stopwords(self) -> None:
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("The quick brown fox")
        assert "the" not in result

    def test_tokenize_filters_short_words(self) -> None:
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("I am a test with many words")
        # Words with 3 or fewer chars are filtered
        assert "test" in result
        assert "with" not in result or len("with") >= 4

    def test_get_top_nouns(self) -> None:
        tokenizer = EnglishTokenizer()
        text = "Computer science studies algorithms and data structures"
        result = tokenizer.get_top_nouns(text, n=3)
        # Should extract nouns
        assert len(result) <= 3
        assert len(result) > 0  # At least one noun

    def test_empty_text(self) -> None:
        tokenizer = EnglishTokenizer()
        result = tokenizer.tokenize("")
        assert result == []

    def test_custom_stopwords(self) -> None:
        tokenizer = EnglishTokenizer(custom_stopwords={"customword"})
        result = tokenizer.tokenize("This is a customword test")
        assert "customword" not in result


class TestTurkishTokenizer:
    """Tests for TurkishTokenizer."""

    def test_tokenize_basic(self) -> None:
        tokenizer = TurkishTokenizer()
        result = tokenizer.tokenize(
            "Hızlı kahverengi tilki tembel köpeğin üzerinden atlar"
        )
        assert "hızlı" in result
        assert "tilki" in result

    def test_tokenize_filters_stopwords(self) -> None:
        tokenizer = TurkishTokenizer()
        result = tokenizer.tokenize("Bir Test Cümlesi")
        # Turkish stopwords like 'bir' should be filtered
        assert "bir" not in result

    def test_get_top_words(self) -> None:
        tokenizer = TurkishTokenizer()
        text = "Test test test kelime kelime"
        result = tokenizer.get_top_words(text, n=2)
        assert len(result) <= 2
        assert "test" in result or "kelime" in result

    def test_empty_text(self) -> None:
        tokenizer = TurkishTokenizer()
        result = tokenizer.tokenize("")
        assert result == []


class TestGermanTokenizer:
    """Tests for GermanTokenizer."""

    def test_tokenize_basic(self) -> None:
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize(
            "Der schnelle braune Fuchs springt über den faulen Hund"
        )
        assert "schnelle" in result
        assert "braune" in result
        assert "fuchs" in result

    def test_tokenize_filters_articles(self) -> None:
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("Der Die Das sind Artikel")
        # Articles should be filtered
        assert "der" not in result
        assert "die" not in result
        assert "das" not in result

    def test_tokenize_preserves_umlauts(self) -> None:
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("Ärzte überprüfen Öffnungszeiten Übungen")
        assert "ärzte" in result
        assert "überprüfen" in result

    def test_tokenize_compound_words(self) -> None:
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("Die Krankenversicherungskarte ist wichtig")
        # Compound word should be preserved
        assert "krankenversicherungskarte" in result

    def test_get_top_words(self) -> None:
        tokenizer = GermanTokenizer()
        text = "Computer Computer Programmierung Software Computer"
        result = tokenizer.get_top_words(text, n=2)
        assert len(result) <= 2
        assert "computer" in result

    def test_empty_text(self) -> None:
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("")
        assert result == []

    def test_custom_stopwords(self) -> None:
        tokenizer = GermanTokenizer(custom_stopwords={"benutzerwort"})
        result = tokenizer.tokenize("Das ist ein benutzerwort Test")
        assert "benutzerwort" not in result

    def test_filters_prepositions(self) -> None:
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("auf dem Tisch mit dem Messer")
        # Prepositions should be filtered
        assert "auf" not in result
        assert "mit" not in result

    def test_filters_conjunctions(self) -> None:
        tokenizer = GermanTokenizer()
        result = tokenizer.tokenize("und oder aber Test Satz")
        # Conjunctions should be filtered
        assert "und" not in result
        assert "oder" not in result
        assert "aber" not in result


class TestTokenizerRegistry:
    """Tests for TokenizerRegistry."""

    def test_register_and_get(self) -> None:
        registry = TokenizerRegistry()
        registry.register("en", EnglishTokenizer())
        registry.register("de", GermanTokenizer())

        assert registry.get("en") is not None
        assert registry.get("de") is not None
        assert registry.get("tr") is None

    def test_get_or_default_with_registered(self) -> None:
        registry = TokenizerRegistry()
        registry.register("de", GermanTokenizer())
        registry.register("en", EnglishTokenizer())

        tokenizer = registry.get_or_default("de")
        assert tokenizer is not None

    def test_get_or_default_fallback_to_english(self) -> None:
        registry = TokenizerRegistry()
        registry.register("en", EnglishTokenizer())

        tokenizer = registry.get_or_default("xx")  # Unknown language
        assert tokenizer is not None
        # Should return English tokenizer
        result = tokenizer.tokenize("The quick brown fox")
        assert "quick" in result

    def test_get_or_default_no_english_raises(self) -> None:
        registry = TokenizerRegistry()
        registry.register("de", GermanTokenizer())

        with pytest.raises(ValueError, match="No tokenizer available"):
            registry.get_or_default("xx")

    def test_supported_languages(self) -> None:
        registry = TokenizerRegistry()
        registry.register("en", EnglishTokenizer())
        registry.register("de", GermanTokenizer())
        registry.register("tr", TurkishTokenizer())

        langs = registry.supported_languages
        assert "en" in langs
        assert "de" in langs
        assert "tr" in langs
        assert len(langs) == 3
