"""Entry point for the PDF Renaming Tool."""

from __future__ import annotations

import sys


def main() -> None:
    """Run the PDF Renaming Tool CLI."""
    from src.cli import cli_entrypoint

    cli_entrypoint()


if __name__ == "__main__":
    main()
