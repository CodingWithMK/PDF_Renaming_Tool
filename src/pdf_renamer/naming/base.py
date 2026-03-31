"""Abstract base class and data models for naming strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class NamingResult:
    """Result of a naming strategy.

    Attributes:
        name: The generated filename (without extension).
        strategy_used: Name of the strategy that generated this result.
    """

    name: str
    strategy_used: str


@dataclass
class ProcessingContext:
    """Context passed to naming strategies.

    Attributes:
        text: The extracted text from the PDF.
        language: Detected ISO 639-1 language code.
        title_candidate: Extracted title if available, None otherwise.
    """

    text: str
    language: str
    title_candidate: str | None = None


class NamingStrategy(ABC):
    """Abstract base class for filename generation strategies.

    Allows adding new naming strategies without modifying existing
    pipeline code (Open/Closed Principle).
    """

    @abstractmethod
    def can_handle(self, context: ProcessingContext) -> bool:
        """Check if this strategy can generate a name for the context.

        Args:
            context: Processing context with text and metadata.

        Returns:
            True if this strategy can handle the context.
        """
        ...

    @abstractmethod
    def generate(self, context: ProcessingContext) -> NamingResult | None:
        """Generate a filename candidate.

        Args:
            context: Processing context with text and metadata.

        Returns:
            NamingResult if successful, None if strategy cannot generate.
        """
        ...
