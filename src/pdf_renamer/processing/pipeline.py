"""Single PDF processing pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from src.pdf_renamer.extraction.base import TextExtractor
from src.pdf_renamer.language.detector import LanguageDetector
from src.pdf_renamer.naming.base import NamingResult, ProcessingContext
from src.pdf_renamer.naming.keyword import KeywordNamingStrategy
from src.pdf_renamer.naming.title import TitleNamingStrategy
from src.pdf_renamer.naming.slugifier import Slugifier
from src.pdf_renamer.processing.renamer import FileRenamer, RenameResult

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of processing a single PDF file.

    Attributes:
        source_path: Original path to the PDF.
        new_name: Generated filename (without extension), None if skipped.
        rename_result: Result of the rename operation, None if not renamed.
        reason: Reason for skipping, None if successfully processed.
    """

    source_path: Path
    new_name: str | None = None
    rename_result: RenameResult | None = None
    reason: str | None = None


class PdfProcessor:
    """Processes a single PDF file through the full pipeline.

    Pipeline steps:
    1. Extract text from the PDF
    2. Detect language
    3. Extract title candidate
    4. Generate filename using naming strategies
    5. Rename the file
    """

    def __init__(
        self,
        extractor: TextExtractor,
        detector: LanguageDetector,
        title_strategy: TitleNamingStrategy,
        keyword_strategy: KeywordNamingStrategy,
        renamer: FileRenamer,
    ) -> None:
        """Initialize the PDF processor.

        Args:
            extractor: Text extractor for PDFs.
            detector: Language detector.
            title_strategy: Strategy for title-based naming.
            keyword_strategy: Strategy for keyword-based naming.
            renamer: File renamer with collision handling.
        """
        self._extractor = extractor
        self._detector = detector
        self._title_strategy = title_strategy
        self._keyword_strategy = keyword_strategy
        self._renamer = renamer

    def process(self, path: Path, max_pages: int = 3) -> ProcessingResult:
        """Process a single PDF file.

        Args:
            path: Path to the PDF file.
            max_pages: Maximum pages to extract text from.

        Returns:
            ProcessingResult with operation status.
        """
        # Step 1: Extract text
        text = self._extractor.extract(path, max_pages)
        if not text.strip():
            logger.info("No text found in %s, skipping", path.name)
            return ProcessingResult(source_path=path, reason="no text")

        # Step 2: Detect language
        language = self._detector.detect(text)
        logger.debug("Detected language '%s' for %s", language, path.name)

        # Step 3: Extract title candidate
        title_candidate = self._extract_title_candidate(path, max_pages)

        # Step 4: Build context
        context = ProcessingContext(
            text=text,
            language=language,
            title_candidate=title_candidate,
        )

        # Step 5: Try naming strategies in order
        naming_result = self._try_naming_strategies(context)
        if naming_result is None:
            logger.info("No name generated for %s, skipping", path.name)
            return ProcessingResult(source_path=path, reason="no name generated")

        # Step 6: Rename
        target_dir = path.parent
        rename_result = self._renamer.rename(path, naming_result.name, target_dir)

        return ProcessingResult(
            source_path=path,
            new_name=naming_result.name,
            rename_result=rename_result,
        )

    def _extract_title_candidate(self, path: Path, max_pages: int = 3) -> str | None:
        """Extract a probable title from the PDF.

        Args:
            path: Path to the PDF file.
            max_pages: Maximum pages to search.

        Returns:
            Title string if found, None otherwise.
        """
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(path))
            num_pages = min(len(reader.pages), max_pages)
            lines: list[str] = []

            for i in range(num_pages):
                page_text = reader.pages[i].extract_text()
                if not page_text:
                    continue
                page_lines = page_text.split("\n")
                filtered = [
                    line.strip() for line in page_lines if len(line.strip()) >= 6
                ]
                lines.extend(filtered)

            if not lines:
                return None

            # Prefer first non-uppercase line of reasonable length
            probable_titles = [
                line for line in lines if (8 < len(line) < 140) and not line.isupper()
            ]
            if probable_titles:
                return probable_titles[0]

            # Fallback to longest line
            return max(lines, key=len)

        except Exception as e:
            logger.warning("Error extracting title from %s: %s", path, e)
            return None

    def _try_naming_strategies(self, context: ProcessingContext) -> NamingResult | None:
        """Try naming strategies in priority order.

        Args:
            context: Processing context.

        Returns:
            First successful NamingResult, or None if all fail.
        """
        strategies = [self._title_strategy, self._keyword_strategy]

        for strategy in strategies:
            if strategy.can_handle(context):
                result = strategy.generate(context)
                if result is not None:
                    logger.debug(
                        "Generated name '%s' using %s strategy",
                        result.name,
                        result.strategy_used,
                    )
                    return result

        return None
