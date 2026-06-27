"""Single-file processing worker for TurboQuery.

Processes a single data file through the full pipeline (load → clean →
tokenize) and builds a local inverted index mapping each token to the
list of ``__row_id`` values where it appears.
"""

from pathlib import Path
from typing import Dict, List

import pandas as pd

from src.cleaner import clean_dataframes
from src.loader import load_files
from src.logger import setup_logger
from src.tokenizer import tokenize

logger = setup_logger(name="worker")


def process_file(filepath: str) -> Dict[str, List[str]]:
    """Process a single file and return its local inverted index.

    The file is loaded, cleaned, and tokenized.  For every row the
    ``searchable_content`` column is tokenized and each resulting token
    is mapped to the row's ``__row_id``.

    Args:
        filepath: Absolute or relative path to a .csv or .json file.

    Returns:
        A dictionary mapping each lowercase token to a list of
        ``__row_id`` strings.  Row IDs are unique per row across the
        whole project (format ``"{filepath}_{row_number}"``).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(filepath).resolve()
    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Step 1: Load the single file via loader (it returns a list).
    dataframes: List[pd.DataFrame] = load_files(str(file_path.parent), verbose=False)

    # Filter to only the target file.
    target_df: pd.DataFrame | None = None
    for df in dataframes:
        src = df["__source_file"].iloc[0] if not df.empty else ""
        if str(file_path) == src:
            target_df = df
            break

    if target_df is None:
        logger.warning("File %s was not loaded by loader, returning empty index.", filepath)
        return {}

    # Step 2: Clean.
    cleaned_list = clean_dataframes([target_df])
    if not cleaned_list:
        return {}
    cleaned = cleaned_list[0]

    # Step 3: Build local inverted index.
    local_index: Dict[str, List[str]] = {}

    for _, row in cleaned.iterrows():
        row_id: str = row["__row_id"]
        content: str = row.get("searchable_content", "")
        tokens: List[str] = tokenize(content)

        for token in tokens:
            if token not in local_index:
                local_index[token] = []
            local_index[token].append(row_id)

    logger.info(
        "Built local index for %s: %d unique tokens, %d rows",
        filepath,
        len(local_index),
        len(cleaned),
    )
    return local_index


if __name__ == "__main__":
    # Simple self-test: process a single file from ./data/.
    import sys

    test_file = "./data/sample01.csv"
    if len(sys.argv) > 1:
        test_file = sys.argv[1]

    print(f"Processing file: {test_file}")
    index = process_file(test_file)
    print(f"  Unique tokens: {len(index)}")
    # Show a few sample entries.
    for i, (token, row_ids) in enumerate(index.items()):
        if i >= 5:
            break
        print(f"  {token!r}: {row_ids[:3]}{'...' if len(row_ids) > 3 else ''}")
    if not index:
        print("  (empty index)")