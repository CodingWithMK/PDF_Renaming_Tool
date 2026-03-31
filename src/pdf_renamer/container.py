"""Dependency injection container for wiring components."""

from __future__ import annotations

from pathlib import Path

from src.pdf_renamer.extraction.pdf import PdfTextExtractor
from src.pdf_renamer.language.detector import LangdetectDetector
from src.pdf_renamer.naming.keyword import KeywordNamingStrategy
from src.pdf_renamer.naming.slugifier import Slugifier
from src.pdf_renamer.naming.title import TitleNamingStrategy
from src.pdf_renamer.orchestrator import RenamerOrchestrator
from src.pdf_renamer.processing.pipeline import PdfProcessor
from src.pdf_renamer.processing.renamer import FileRenamer
from src.pdf_renamer.tokenization.english import EnglishTokenizer
from src.pdf_renamer.tokenization.german import GermanTokenizer
from src.pdf_renamer.tokenization.registry import TokenizerRegistry
from src.pdf_renamer.tokenization.turkish import TurkishTokenizer


class Container:
    """Wires all dependencies for the PDF renaming tool.

    This replaces hard-coded imports and allows for easy testing
    by substituting mock implementations.
    """

    def __init__(
        self,
        *,
        dry_run: bool = False,
        transliterate_german: bool = False,
    ) -> None:
        """Initialize the container with all dependencies.

        Args:
            dry_run: If True, simulate renames without modifying files.
            transliterate_german: If True, convert German umlauts to ASCII.
        """
        # Core components
        self.text_extractor = PdfTextExtractor()
        self.language_detector = LangdetectDetector()
        self.slugifier = Slugifier(transliterate_german=transliterate_german)
        self.file_renamer = FileRenamer(dry_run=dry_run)

        # Tokenizer registry with language support
        self.tokenizer_registry = self._build_tokenizer_registry()

        # Naming strategies
        self.title_strategy = TitleNamingStrategy(self.slugifier)
        self.keyword_strategy = KeywordNamingStrategy(
            self.tokenizer_registry, self.slugifier
        )

        # Pipeline
        self.pipeline = PdfProcessor(
            extractor=self.text_extractor,
            detector=self.language_detector,
            title_strategy=self.title_strategy,
            keyword_strategy=self.keyword_strategy,
            renamer=self.file_renamer,
        )

        # Orchestrator
        self.orchestrator = RenamerOrchestrator(self.pipeline)

    def _build_tokenizer_registry(self) -> TokenizerRegistry:
        """Build and populate the tokenizer registry.

        Returns:
            TokenizerRegistry with English, Turkish, and German tokenizers.
        """
        registry = TokenizerRegistry()
        registry.register("en", EnglishTokenizer())
        registry.register("tr", TurkishTokenizer())
        registry.register("de", GermanTokenizer())
        return registry

    def run(self, directory: str | Path, max_pages: int = 3) -> None:
        """Run the PDF renaming tool on a directory.

        Args:
            directory: Path to the directory containing PDFs.
            max_pages: Maximum pages to extract from each PDF.
        """
        self.orchestrator.run(Path(directory), max_pages)
