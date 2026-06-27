"""Index merging utilities for TurboQuery.

Provides functions to merge multiple inverted indexes into a single
consolidated index, with optional deduplication of row IDs.
"""

from typing import Dict, List

from src.logger import setup_logger

logger = setup_logger(name="merger")


def merge_indexes(
    *indexes: Dict[str, List[str]],
    deduplicate: bool = True,
) -> Dict[str, List[str]]:
    """Merge multiple inverted indexes into one.

    Takes any number of token→row_ids dictionaries and combines them.
    When the same token appears in multiple indexes, the row ID lists
    are concatenated.  If ``deduplicate`` is True (the default),
    duplicate row IDs for a given token are removed while preserving
    insertion order.

    Args:
        *indexes: One or more inverted index dictionaries.  Each is a
            mapping of ``{token: [row_id, ...]}``.
        deduplicate: If True, remove duplicate row IDs per token.
            Defaults to True.

    Returns:
        A single merged inverted index dictionary.

    Example:
        >>> idx1 = {"hello": ["a_1", "a_2"], "world": ["a_1"]}
        >>> idx2 = {"hello": ["b_1"], "foo": ["b_2"]}
        >>> merge_indexes(idx1, idx2)
        {"hello": ["a_1", "a_2", "b_1"], "world": ["a_1"], "foo": ["b_2"]}
    """
    merged: Dict[str, List[str]] = {}

    for idx in indexes:
        for token, row_ids in idx.items():
            if token not in merged:
                merged[token] = []
            merged[token].extend(row_ids)

    if deduplicate:
        for token in merged:
            # Preserve order while removing duplicates.
            seen: set = set()
            deduped: List[str] = []
            for rid in merged[token]:
                if rid not in seen:
                    seen.add(rid)
                    deduped.append(rid)
            merged[token] = deduped

    logger.info(
        "Merged %d index(es) → %d unique tokens",
        len(indexes),
        len(merged),
    )
    return merged


if __name__ == "__main__":
    # Simple self-test.
    idx_a: Dict[str, List[str]] = {
        "apple": ["data/a.csv_0", "data/a.csv_3"],
        "banana": ["data/a.csv_1"],
    }
    idx_b: Dict[str, List[str]] = {
        "apple": ["data/b.json_0", "data/a.csv_0"],  # duplicate row ID
        "cherry": ["data/b.json_2"],
    }

    print("Index A:", idx_a)
    print("Index B:", idx_b)
    result = merge_indexes(idx_a, idx_b)
    print("Merged:", result)
    # Expected: apple has 3 unique IDs (a_0, a_3, b_0), banana has 1, cherry has 1.
    assert len(result["apple"]) == 3, f"Expected 3, got {len(result['apple'])}"
    assert len(result["banana"]) == 1
    assert len(result["cherry"]) == 1
    print("All assertions passed.")