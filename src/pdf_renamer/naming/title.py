"""Title-based naming strategy."""

from __future__ import annotations

from src.pdf_renamer.naming.base import NamingResult, NamingStrategy, ProcessingContext
from src.pdf_renamer.naming.slugifier import Slugifier


class TitleNamingStrategy(NamingStrategy):
    """Generates filenames from extracted PDF titles.

    This strategy is preferred when a title can be extracted,
    as it typically produces the most meaningful filenames.
    """

    def __init__(self, slugifier: Slugifier | None = None) -> None:
        """Initialize with optional slugifier.

        Args:
            slugifier: Slugifier instance. Creates default if None.
        """
        self._slugifier = slugifier or Slugifier()

    def can_handle(self, context: ProcessingContext) -> bool:
        """Check if a title candidate is available.

        Args:
            context: Processing context.

        Returns:
            True if a title candidate exists and is suitable for naming.
        """
        if context.title_candidate is None:
            return False

        title = context.title_candidate.strip()

        # Title must be non-empty and reasonable length
        if len(title) < 4 or len(title) > 140:
            return False

        # Skip all-uppercase titles (likely headers/metadata)
        return not title.isupper()

    def generate(self, context: ProcessingContext) -> NamingResult | None:
        """Generate a filename from the title candidate.

        Args:
            context: Processing context with title candidate.

        Returns:
            NamingResult with slugified title, or None if not applicable.
        """
        if not self.can_handle(context):
            return None

        # After can_handle() returns True, title_candidate is guaranteed to be str
        title = context.title_candidate
        assert title is not None  # Type guard for type checker

        slug = self._slugifier.sanitize(title, context.language)

        return NamingResult(name=slug, strategy_used="title")
