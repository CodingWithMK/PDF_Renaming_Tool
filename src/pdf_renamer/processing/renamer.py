"""File renaming with collision resolution."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class RenameResult:
    """Result of a file rename operation.

    Attributes:
        original_path: The original file path.
        new_path: The new file path after renaming.
        success: Whether the rename operation succeeded.
        error: Error message if the operation failed, None otherwise.
    """

    original_path: Path
    new_path: Path
    success: bool
    error: str | None = None


class FileRenamer:
    """Handles file renaming with collision-safe suffixing.

    When a file with the target name already exists, automatically
    appends an incrementing suffix (_1, _2, etc.) to avoid overwriting.
    """

    def __init__(self, *, dry_run: bool = False) -> None:
        """Initialize the file renamer.

        Args:
            dry_run: If True, simulate renames without modifying files.
        """
        self._dry_run = dry_run

    def rename(self, source: Path, new_name: str, target_dir: Path) -> RenameResult:
        """Rename a file with collision-safe suffixing.

        Args:
            source: Path to the original file.
            new_name: Desired filename without extension.
            target_dir: Target directory for the renamed file.

        Returns:
            RenameResult with operation status.
        """
        ext = ".pdf"
        new_filename = f"{new_name}{ext}"
        new_filepath = target_dir / new_filename

        # Handle collisions
        counter = 1
        while new_filepath.exists():
            new_filename = f"{new_name}_{counter}{ext}"
            new_filepath = target_dir / new_filename
            counter += 1

        if self._dry_run:
            logger.info("[DRY RUN] Would rename: %s -> %s", source.name, new_filename)
            return RenameResult(
                original_path=source,
                new_path=new_filepath,
                success=True,
            )

        try:
            os.rename(str(source), str(new_filepath))
            logger.info("Renamed: %s -> %s", source.name, new_filename)
            return RenameResult(
                original_path=source,
                new_path=new_filepath,
                success=True,
            )
        except OSError as e:
            logger.error("Failed to rename %s: %s", source, e)
            return RenameResult(
                original_path=source,
                new_path=new_filepath,
                success=False,
                error=str(e),
            )
