"""Command-line interface for the PDF Renaming Tool."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.pdf_renamer.container import Container


def setup_logging(verbose: bool = False, log_file: Path | None = None) -> None:
    """Configure logging based on verbosity level.

    Args:
        verbose: If True, enable DEBUG level logging.
        log_file: Optional path to write log output to.
    """
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(level=level, format=fmt, handlers=handlers)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Command-line arguments. If None, uses sys.argv.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        prog="pdf-renaming-tool",
        description="Rename PDF files based on content analysis (titles, keywords).",
        epilog="Example: pdf-renaming-tool ./my-pdfs --dry-run --verbose",
    )

    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing PDF files to rename.",
    )

    parser.add_argument(
        "-n",
        "--max-pages",
        type=int,
        default=3,
        metavar="N",
        help="Maximum number of pages to extract text from (default: 3).",
    )

    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Simulate renames without modifying files.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable detailed logging output.",
    )

    parser.add_argument(
        "--transliterate-german",
        action="store_true",
        help="Convert German umlauts (ae, oe, ue, ss) in filenames.",
    )

    parser.add_argument(
        "--log-file",
        type=Path,
        metavar="PATH",
        help="Write log output to the specified file.",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the PDF Renaming Tool CLI.

    Args:
        argv: Command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    args = parse_args(argv)

    # Setup logging
    setup_logging(verbose=args.verbose, log_file=args.log_file)

    # Validate directory
    if not args.directory.is_dir():
        logging.error("Directory not found: %s", args.directory)
        return 1

    # Print configuration
    logging.info("PDF Renaming Tool")
    logging.info("=" * 40)
    logging.info("Directory:    %s", args.directory.resolve())
    logging.info("Max pages:    %d", args.max_pages)
    logging.info("Dry run:      %s", args.dry_run)
    logging.info("Transliterate: %s", args.transliterate_german)
    logging.info("=" * 40)

    # Create container and run
    container = Container(
        dry_run=args.dry_run,
        transliterate_german=args.transliterate_german,
    )

    try:
        result = container.orchestrator.run(args.directory, args.max_pages)
        logging.info("")
        logging.info("Summary:")
        logging.info("  Total PDFs found: %d", result.total)
        logging.info("  Renamed:          %d", len(result.processed))
        logging.info("  Skipped:          %d", len(result.skipped))

        if args.verbose and result.skipped:
            logging.info("")
            logging.info("Skipped files:")
            for r in result.skipped:
                logging.info("  - %s: %s", r.source_path.name, r.reason)

        return 0

    except Exception as e:
        logging.error("Error: %s", e)
        if args.verbose:
            logging.exception("Traceback:")
        return 1


def cli_entrypoint() -> None:
    """Entry point for the CLI script."""
    sys.exit(main())
