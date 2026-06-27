"""TurboQuery CLI — inverted-index keyword search over CSV/JSON files.

Usage:
    python -m src.main --input ./data --query "keywords" --mode and --format terminal

Required: --input (directory), --query (space-separated keywords).
Optional: --mode (and|or, default and), --output, --format (terminal|json|csv), --verbose.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.cleaner import clean_dataframes
from src.config import DEFAULT_INPUT
from src.formatter import format_csv, format_json, format_terminal
from src.indexer import build_global_index
from src.loader import load_files
from src.logger import setup_logger
from src.querier import execute_query

logger = setup_logger(name="main")


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="TurboQuery — fast keyword search over CSV/JSON files.",
    )
    parser.add_argument(
        "--input", required=True,
        help="Directory containing .csv/.json files.",
    )
    parser.add_argument(
        "--query", required=True,
        help="Space-separated keywords to search for.",
    )
    parser.add_argument(
        "--mode", default="and", choices=["and", "or"],
        help="Matching mode: 'and' (all) or 'or' (any). Default: and.",
    )
    parser.add_argument(
        "--output", default=None,
        help="Output file path (stdout if not set; CSV defaults to ./query_results.csv).",
    )
    parser.add_argument(
        "--format", default="terminal", choices=["terminal", "json", "csv"],
        help="Output format. Default: terminal.",
    )
    parser.add_argument(
        "--verbose", action="store_true",
        help="Enable DEBUG-level logging.",
    )
    return parser.parse_args(argv)


def _split_keywords(query: str) -> List[str]:
    """Split a space-separated query string into keyword list."""
    return [kw.strip() for kw in query.split() if kw.strip()]


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for TurboQuery CLI. Returns 0 on success, non-zero on error."""
    args = _parse_args(argv)
    if args.verbose:
        logger.setLevel("DEBUG")

    keywords: List[str] = _split_keywords(args.query)
    if not keywords:
        logger.error("Empty query. Provide space-separated keywords.")
        return 1

    input_dir: str = args.input

    # Step 1: Load and clean DataFrames
    logger.info("Loading data from: %s", input_dir)
    try:
        dataframes: List[pd.DataFrame] = load_files(input_dir, verbose=args.verbose)
    except FileNotFoundError as exc:
        logger.error("Load error: %s", exc)
        return 2
    except Exception as exc:
        logger.error("Unexpected load error: %s", exc)
        return 3

    if not dataframes:
        logger.error("No supported files in %s", input_dir)
        return 4

    logger.info("Cleaning %d DataFrame(s)...", len(dataframes))
    try:
        cleaned_dfs: List[pd.DataFrame] = clean_dataframes(dataframes)
    except Exception as exc:
        logger.error("Cleaning error: %s", exc)
        return 5

    # Step 2: Build global inverted index
    logger.info("Building global inverted index...")
    try:
        global_index: Dict[str, List[str]] = build_global_index(
            directory=input_dir,
            verbose=args.verbose,
        )
    except Exception as exc:
        logger.error("Indexing error: %s", exc)
        return 6

    if not global_index:
        logger.warning("Global index is empty.")

    # Step 3: Execute query
    logger.info("Executing: %s (mode=%s)", keywords, args.mode)
    try:
        results: List[Dict[str, Any]] = execute_query(
            index=global_index,
            dataframes=cleaned_dfs,
            keywords=keywords,
            mode=args.mode,
        )
    except ValueError as exc:
        logger.error("Query error: %s", exc)
        return 7
    except Exception as exc:
        logger.error("Unexpected query error: %s", exc)
        return 8

    # Step 4: Format and output
    output_file: Optional[str] = args.output
    fmt: str = args.format

    try:
        if fmt == "terminal":
            format_terminal(results, file=output_file)
        elif fmt == "json":
            format_json(results, file=output_file)
        elif fmt == "csv":
            csv_path: str = format_csv(results, output_path=output_file)
            logger.info("Results written to: %s", csv_path)
        else:
            logger.error("Unknown format: %s", fmt)
            return 9
    except Exception as exc:
        logger.error("Format/output error: %s", exc)
        return 10

    logger.info("Done — %d result(s).", len(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())