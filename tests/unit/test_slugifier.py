"""Unit tests for the slugify function."""

from __future__ import annotations

import pytest

from pdf_renamer import slugify


class TestSlugify:
    """Tests for slugify()."""

    def test_replaces_spaces_with_underscores(self) -> None:
        result = slugify("Hello World", "en")
        assert result == "Hello_World"

    def test_removes_angle_brackets(self) -> None:
        result = slugify("Hello<World>", "en")
        assert result == "HelloWorld"

    def test_removes_colon(self) -> None:
        result = slugify("Hello: World", "en")
        assert result == "Hello_World"

    def test_removes_quotes(self) -> None:
        result = slugify('Hello "World"', "en")
        assert result == "Hello_World"

    def test_removes_backslash(self) -> None:
        result = slugify("Hello\\World", "en")
        assert result == "HelloWorld"

    def test_removes_pipe(self) -> None:
        result = slugify("Hello|World", "en")
        assert result == "HelloWorld"

    def test_removes_question_mark(self) -> None:
        result = slugify("Hello?World", "en")
        assert result == "HelloWorld"

    def test_removes_asterisk(self) -> None:
        result = slugify("Hello*World", "en")
        assert result == "HelloWorld"

    def test_strips_whitespace(self) -> None:
        result = slugify("  Hello World  ", "en")
        assert result == "Hello_World"

    def test_preserves_turkish_chars(self) -> None:
        result = slugify("İstanbul Şehir", "tr")
        assert "İstanbul" in result
        assert "Şehir" in result

    def test_preserves_turkish_chars_in_en_mode(self) -> None:
        # Turkish chars are preserved by default (transliteration commented out)
        result = slugify("İstanbul", "en")
        assert "İstanbul" in result

    def test_empty_string(self) -> None:
        result = slugify("", "en")
        assert result == ""

    def test_no_special_chars(self) -> None:
        result = slugify("SimpleTitle", "en")
        assert result == "SimpleTitle"

    def test_multiple_special_chars(self) -> None:
        result = slugify("A:B/C\\D|E*F?G", "en")
        assert result == "ABCDEFG"

    def test_complex_turkish_title(self) -> None:
        result = slugify("Bilgisayar Bilimleri: Giriş", "tr")
        assert "Bilgisayar_Bilimleri" in result
        assert "Giriş" in result
