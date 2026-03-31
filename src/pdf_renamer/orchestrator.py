"""Batch processing orchestrator for multiple PDFs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from src.pdf_renamer.processing.pipeline import PdfProcessor, ProcessingResult

logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of batch processing multiple PDFs.

    Attributes:
        processed: List of successfully processed results.
        skipped: List of skipped results with reasons.
        total: Total number of PDFs found.
    """

    processed: list[ProcessingResult] = field(default_factory=list)
    skipped: list[ProcessingResult] = field(default_factory=list)
    total: int = 0


class RenamerOrchestrator:
    """Orchestrates batch processing of PDF files in a directory.

    Discovers PDF files and processes each through the PdfProcessor pipeline.
    """

    def __init__(self, pipeline: PdfProcessor) -> None:
        """Initialize the orchestrator.

        Args:
            pipeline: PdfProcessor instance to use for each file.
        """
        self._pipeline = pipeline

    def run(
        self,
        directory: Path,
        max_pages: int = 3,
        pattern: str = "*.pdf",
    ) -> BatchResult:
        """Process all PDFs in a directory.

        Args:
            directory: Directory containing PDF files.
            max_pages: Maximum pages to extract from each PDF.
            pattern: Glob pattern for file discovery (case-insensitive).

        Returns:
            BatchResult with all processing outcomes.
        """
        if not directory.is_dir():
            logger.error("Directory not found: %s", directory)
            return BatchResult()

        # Discover PDF files (case-insensitive)
        pdf_files = list(directory.glob(pattern)) + list(
            directory.glob(pattern.upper())
        )
        # Deduplicate
        pdf_files = list(set(pdf_files))
        pdf_files.sort()

        logger.info("Found %d PDF files in %s", len(pdf_files), directory)

        result = BatchResult(total=len(pdf_files))

        for pdf_path in pdf_files:
            proc_result = self._pipeline.process(pdf_path, max_pages)

            if proc_result.reason is not None:
                result.skipped.append(proc_result)
            else:
                result.processed.append(proc_result)

        logger.info(
            "Processing complete: %d renamed, %d skipped",
            len(result.processed),
            len(result.skipped),
        )

        return result
