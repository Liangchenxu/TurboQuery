"""Data cleaning and normalization module for TurboQuery.

Receives a list of DataFrames, normalizes column names, fills missing
values, merges text columns into a searchable content column, and
assigns a globally unique row ID.
"""

from typing import List

import pandas as pd

from src.logger import setup_logger

logger = setup_logger(name="cleaner")

# Columns that carry metadata rather than user-facing text content.
# These are excluded when building the searchable_content column.
_META_COLUMNS = {"__source_file", "__row_id", "id", "工号", "employee_id"}


def _normalize_column_name(name: str) -> str:
    """Normalize a single column name to lowercase with underscores.

    Replaces spaces, hyphens, and consecutive non-alphanumeric
    characters with a single underscore. Strips leading/trailing
    underscores.

    Args:
        name: Original column name.

    Returns:
        Normalized column name string.
    """
    import re

    # Convert to lowercase.
    normalized = name.lower()
    # Replace any run of non-alphanumeric characters (except underscore) with '_'.
    normalized = re.sub(r"[^a-z0-9_]+", "_", normalized)
    # Collapse multiple underscores.
    normalized = re.sub(r"_+", "_", normalized)
    # Strip leading/trailing underscores.
    normalized = normalized.strip("_")
    return normalized if normalized else "unnamed_column"


def clean_dataframes(
    dataframes: List[pd.DataFrame],
) -> List[pd.DataFrame]:
    """Clean and normalize a list of DataFrames.

    For each DataFrame the following operations are performed:

    1. Column names are normalized to lowercase_with_underscores.
    2. All NaN/None values are filled with the empty string ``""``.
    3. A ``__row_id`` column is added with the format
       ``"{filename}_{row_number}"`` (1-based row number).
    4. Non-metadata text columns are merged into a single
       ``searchable_content`` column (space-separated).

    Args:
        dataframes: List of DataFrames as returned by ``loader.load_files``.
            Each DataFrame must contain a ``__source_file`` column.

    Returns:
        A new list of cleaned DataFrames. The original DataFrames are
        not modified.

    Raises:
        ValueError: If any DataFrame is missing the ``__source_file`` column.
    """
    cleaned: List[pd.DataFrame] = []

    for idx, df in enumerate(dataframes):
        if "__source_file" not in df.columns:
            raise ValueError(
                f"DataFrame at index {idx} is missing '__source_file' column"
            )

        # Work on a copy to avoid mutating the original.
        df_clean = df.copy()

        # 1. Normalize column names.
        df_clean.columns = [_normalize_column_name(c) for c in df_clean.columns]

        # 2. Fill missing values with empty string.
        df_clean = df_clean.fillna("")

        # 3. Add globally unique row ID.
        source_file = df_clean["__source_file"].iloc[0]
        # Use 1-based row numbering.
        row_numbers = range(1, len(df_clean) + 1)
        df_clean["__row_id"] = [
            f"{source_file}_{n}" for n in row_numbers
        ]

        # 4. Build searchable_content from non-metadata text columns.
        text_columns = [
            col
            for col in df_clean.columns
            if col not in _META_COLUMNS
        ]
        if text_columns:
            # Concatenate all text columns with a space separator.
            df_clean["searchable_content"] = (
                df_clean[text_columns]
                .astype(str)
                .agg(" ".join, axis=1)
            )
        else:
            df_clean["searchable_content"] = ""

        logger.info(
            "Cleaned DataFrame from %s: %d rows, %d columns",
            source_file,
            len(df_clean),
            len(df_clean.columns),
        )
        cleaned.append(df_clean)

    logger.info("Cleaned %d DataFrame(s)", len(cleaned))
    return cleaned


if __name__ == "__main__":
    # Simple self-test: load files and run the cleaner on them.
    from src.loader import load_files

    test_dir = "./data"
    print(f"Loading and cleaning files from: {test_dir}")
    frames = load_files(test_dir, verbose=False)
    if not frames:
        print("  No files to clean.")
    else:
        cleaned_frames = clean_dataframes(frames)
        for i, cf in enumerate(cleaned_frames):
            src = cf["__source_file"].iloc[0]
            print(f"  [{i}] {src}")
            print(f"       Columns: {list(cf.columns)}")
            print(f"       Sample row_id: {cf['__row_id'].iloc[0]}")
            print(f"       Sample searchable_content: {cf['searchable_content'].iloc[0][:80]}...")