"""Unit tests for language detector."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.pdf_renamer.language.detector import LangdetectDetector


class TestLangdetectDetector:
    """Tests for LangdetectDetector."""

    @patch("langdetect.detect")
    def test_detect_english(self, mock_detect: MagicMock) -> None:
        mock_detect.return_value = "en"
        detector = LangdetectDetector()
        result = detector.detect("This is an English sentence")
        assert result == "en"

    @patch("langdetect.detect")
    def test_detect_german(self, mock_detect: MagicMock) -> None:
        mock_detect.return_value = "de"
        detector = LangdetectDetector()
        result = detector.detect("Das ist ein deutscher Satz")
        assert result == "de"

    @patch("langdetect.detect")
    def test_detect_turkish(self, mock_detect: MagicMock) -> None:
        mock_detect.return_value = "tr"
        detector = LangdetectDetector()
        result = detector.detect("Bu bir Türkçe cümledir")
        assert result == "tr"

    @patch("langdetect.detect")
    def test_detect_failure_defaults_to_english(self, mock_detect: MagicMock) -> None:
        mock_detect.side_effect = Exception("Detection failed")
        detector = LangdetectDetector()
        result = detector.detect("Some text")
        assert result == "en"

    @patch("langdetect.detect")
    def test_detect_short_text(self, mock_detect: MagicMock) -> None:
        mock_detect.return_value = "en"
        detector = LangdetectDetector()
        result = detector.detect("Hi")
        assert result == "en"
