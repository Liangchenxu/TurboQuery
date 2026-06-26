"""File scanning and parsing module for TurboQuery.

Scans a directory for .csv and .json files, detects encoding with
GBK/UTF-8 auto-detection, reads them with pandas, and returns a list
of DataFrames with a ``__source_file`` column attached.
"""

import json
import os
from pathlib import Path
from typing import List, Optional

import pandas as pd

from src.logger import setup_logger

logger = setup_logger(name="loader")


def _detect_encoding(filepath: str) -> str:
    """Attempt to detect the encoding of a text file.

    Tries UTF-8 first, then GBK. Falls back to UTF-8 with error
    replacement if both fail.

    Args:
        filepath: Absolute or relative path to the file.

    Returns:
        The detected encoding string (e.g. 'utf-8', 'gbk').
    """
    encodings_to_try = ["utf-8", "gbk"]
    for enc in encodings_to_try:
        try:
            with open(filepath, "r", encoding=enc) as fh:
                fh.read(4096)
            logger.debug("Detected encoding %s for %s", enc, filepath)
            return enc
        except (UnicodeDecodeError, LookupError):
            continue
    logger.warning(
        "Could not detect encoding for %s, falling back to utf-8 with replace",
        filepath,
    )
    return "utf-8"


def _read_csv_safe(filepath: str, encoding: str) -> Optional[pd.DataFrame]:
    """Read a CSV file into a DataFrame, handling encoding issues.

    Args:
        filepath: Path to the CSV file.
        encoding: Encoding to use for reading.

    Returns:
        A pandas DataFrame or None if reading fails.
    """
    try:
        df = pd.read_csv(
            filepath,
            encoding=encoding,
            encoding_errors="replace",
            dtype=str,
            keep_default_na=False,
        )
        logger.info("Loaded CSV: %s (%d rows)", filepath, len(df))
        return df
    except Exception as exc:
        logger.error("Failed to read CSV %s: %s", filepath, exc)
        return None


def _read_json_safe(filepath: str, encoding: str) -> Optional[pd.DataFrame]:
    """Read a JSON file (array of objects) into a DataFrame.

    Args:
        filepath: Path to the JSON file.
        encoding: Encoding to use for reading.

    Returns:
        A pandas DataFrame or None if reading fails.
    """
    try:
        with open(filepath, "r", encoding=encoding, errors="replace") as fh:
            data = json.load(fh)
        if isinstance(data, list):
            df = pd.DataFrame(data, dtype=str)
        elif isinstance(data, dict):
            # If the JSON is a single object, wrap it in a list.
            df = pd.DataFrame([data], dtype=str)
        else:
            logger.warning("Unsupported JSON structure in %s, skipping.", filepath)
            return None
        logger.info("Loaded JSON: %s (%d rows)", filepath, len(df))
        return df
    except Exception as exc:
        logger.error("Failed to read JSON %s: %s", filepath, exc)
        return None


def load_files(
    directory: str,
    verbose: bool = False,
) -> List[pd.DataFrame]:
    """Scan a directory and load all .csv and .json files into DataFrames.

    Each returned DataFrame has an additional column ``__source_file``
    that records the absolute path of the originating file.

    Args:
        directory: Path to the directory containing data files.
        verbose: If True, enable DEBUG-level logging.

    Returns:
        A list of pandas DataFrames, one per successfully loaded file.
        Files that fail to parse are skipped with a warning.

    Raises:
        FileNotFoundError: If the provided directory does not exist.
    """
    if verbose:
        logger.setLevel("DEBUG")

    dir_path = Path(directory).resolve()
    if not dir_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    dataframes: List[pd.DataFrame] = []
    supported_extensions = {".csv", ".json"}

    for file_path in sorted(dir_path.iterdir()):
        if file_path.suffix.lower() not in supported_extensions:
            logger.debug("Skipping unsupported file: %s", file_path)
            continue
        if not file_path.is_file():
            continue

        abs_path = str(file_path.resolve())
        encoding = _detect_encoding(abs_path)

        if file_path.suffix.lower() == ".csv":
            df = _read_csv_safe(abs_path, encoding)
        else:  # .json
            df = _read_json_safe(abs_path, encoding)

        if df is not None:
            df["__source_file"] = abs_path
            dataframes.append(df)

    logger.info("Loaded %d file(s) from %s", len(dataframes), dir_path)
    return dataframes


if __name__ == "__main__":
    # Simple self-test: load files from the default data directory.
    import sys

    test_dir = "./data"
    if len(sys.argv) > 1:
        test_dir = sys.argv[1]

    print(f"Loading files from: {test_dir}")
    frames = load_files(test_dir, verbose=True)
    for i, frame in enumerate(frames):
        src = frame["__source_file"].iloc[0] if not frame.empty else "unknown"
        print(f"  [{i}] {src} — {len(frame)} rows, {len(frame.columns)} columns")
    if not frames:
        print("  No files loaded.")