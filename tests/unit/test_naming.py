"""Unit tests for naming strategies and slugifier."""

from __future__ import annotations

from src.pdf_renamer.naming.base import ProcessingContext
from src.pdf_renamer.naming.keyword import KeywordNamingStrategy
from src.pdf_renamer.naming.slugifier import Slugifier
from src.pdf_renamer.naming.title import TitleNamingStrategy
from src.pdf_renamer.tokenization.english import EnglishTokenizer
from src.pdf_renamer.tokenization.german import GermanTokenizer
from src.pdf_renamer.tokenization.registry import TokenizerRegistry


class TestSlugifier:
    """Tests for Slugifier."""

    def test_sanitize_basic(self) -> None:
        slugifier = Slugifier()
        result = slugifier.sanitize("Hello World", "en")
        assert result == "Hello_World"

    def test_sanitize_removes_invalid_chars(self) -> None:
        slugifier = Slugifier()
        result = slugifier.sanitize('Hello: "World" <Test>', "en")
        assert ":" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result

    def test_sanitize_preserves_german_umlauts_by_default(self) -> None:
        slugifier = Slugifier()
        result = slugifier.sanitize("Ärzte über Öffnungen", "de")
        assert "Ärzte" in result
        assert "über" in result
        assert "Öffnungen" in result

    def test_sanitize_transliterates_german_when_enabled(self) -> None:
        slugifier = Slugifier(transliterate_german=True)
        result = slugifier.sanitize("Ärzte über Öffnungen", "de")
        assert "Ae" in result or "ae" in result
        assert "Oe" in result or "oe" in result

    def test_sanitize_preserves_turkish_chars(self) -> None:
        slugifier = Slugifier()
        result = slugifier.sanitize("İstanbul Şehir", "tr")
        assert "İstanbul" in result
        assert "Şehir" in result

    def test_sanitize_strips_whitespace(self) -> None:
        slugifier = Slugifier()
        result = slugifier.sanitize("  Hello World  ", "en")
        assert result == "Hello_World"

    def test_sanitize_empty_string(self) -> None:
        slugifier = Slugifier()
        result = slugifier.sanitize("", "en")
        assert result == ""


class TestTitleNamingStrategy:
    """Tests for TitleNamingStrategy."""

    def test_can_handle_with_valid_title(self) -> None:
        strategy = TitleNamingStrategy()
        context = ProcessingContext(
            text="some text",
            language="en",
            title_candidate="A Valid Title Here",
        )
        assert strategy.can_handle(context) is True

    def test_cannot_handle_none_title(self) -> None:
        strategy = TitleNamingStrategy()
        context = ProcessingContext(
            text="some text",
            language="en",
            title_candidate=None,
        )
        assert strategy.can_handle(context) is False

    def test_cannot_handle_short_title(self) -> None:
        strategy = TitleNamingStrategy()
        context = ProcessingContext(
            text="some text",
            language="en",
            title_candidate="Hi",
        )
        assert strategy.can_handle(context) is False

    def test_cannot_handle_all_uppercase_title(self) -> None:
        strategy = TitleNamingStrategy()
        context = ProcessingContext(
            text="some text",
            language="en",
            title_candidate="ALL UPPERCASE TITLE",
        )
        assert strategy.can_handle(context) is False

    def test_generate_returns_slugified_title(self) -> None:
        strategy = TitleNamingStrategy()
        context = ProcessingContext(
            text="some text",
            language="en",
            title_candidate="My Document Title",
        )
        result = strategy.generate(context)
        assert result is not None
        assert result.name == "My_Document_Title"
        assert result.strategy_used == "title"

    def test_generate_returns_none_for_invalid(self) -> None:
        strategy = TitleNamingStrategy()
        context = ProcessingContext(
            text="some text",
            language="en",
            title_candidate=None,
        )
        result = strategy.generate(context)
        assert result is None


class TestKeywordNamingStrategy:
    """Tests for KeywordNamingStrategy."""

    def _make_registry(self) -> TokenizerRegistry:
        registry = TokenizerRegistry()
        registry.register("en", EnglishTokenizer())
        registry.register("de", GermanTokenizer())
        return registry

    def test_can_handle_with_registered_language(self) -> None:
        registry = self._make_registry()
        strategy = KeywordNamingStrategy(registry)
        context = ProcessingContext(text="test", language="en")
        assert strategy.can_handle(context) is True

    def test_cannot_handle_unregistered_language(self) -> None:
        registry = self._make_registry()
        strategy = KeywordNamingStrategy(registry)
        context = ProcessingContext(text="test", language="xx")
        assert strategy.can_handle(context) is False

    def test_generate_returns_keyword(self) -> None:
        registry = self._make_registry()
        strategy = KeywordNamingStrategy(registry)
        context = ProcessingContext(
            text="Algorithm analysis complexity performance benchmark",
            language="en",
        )
        result = strategy.generate(context)
        assert result is not None
        assert result.strategy_used == "keyword"
        # Should be a meaningful word, not a stopword
        assert len(result.name) >= 4

    def test_generate_german_keyword(self) -> None:
        registry = self._make_registry()
        strategy = KeywordNamingStrategy(registry)
        context = ProcessingContext(
            text="Programmierung Algorithmen Datenstrukturen Analyse",
            language="de",
        )
        result = strategy.generate(context)
        assert result is not None
        assert result.strategy_used == "keyword"

    def test_generate_empty_text_returns_none(self) -> None:
        registry = self._make_registry()
        strategy = KeywordNamingStrategy(registry)
        context = ProcessingContext(text="", language="en")
        result = strategy.generate(context)
        assert result is None

    def test_generate_only_stopwords_returns_none(self) -> None:
        registry = self._make_registry()
        strategy = KeywordNamingStrategy(registry)
        context = ProcessingContext(text="the and or but", language="en")
        result = strategy.generate(context)
        assert result is None
