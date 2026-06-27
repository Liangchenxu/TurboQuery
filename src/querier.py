"""Query execution module for TurboQuery.

Looks up query tokens in the global inverted index, extracts matching
rows from the cleaned DataFrames, and returns structured result objects
with file path, row ID, context snippet, and matched keywords.
"""

from typing import Any, Dict, List, Optional

import pandas as pd

from src.config import MAX_CONTEXT_LENGTH
from src.logger import setup_logger
from src.tokenizer import tokenize

logger = setup_logger(name="querier")


def execute_query(
    index: Dict[str, List[str]],
    dataframes: List[pd.DataFrame],
    keywords: List[str],
    mode: str = "and",
    max_context_length: int = MAX_CONTEXT_LENGTH,
) -> List[Dict[str, Any]]:
    """Execute a keyword search against the global inverted index.

    Tokenizes each keyword, looks up matching row IDs, applies AND/OR
    logic, and extracts context snippets from the ``searchable_content``
    column of each matched row.

    Args:
        index: The global inverted index mapping tokens to lists of
            ``__row_id`` strings (``{token: [row_id, ...]}``).
        dataframes: A list of cleaned DataFrames (with ``__row_id``,
            ``__source_file``, and ``searchable_content`` columns) as
            produced by :func:`src.cleaner.clean_dataframes`.
        keywords: A list of raw keyword strings (e.g., ``["张三", "技术部"]``).
        mode: Matching mode — ``"and"`` requires all keyword tokens to
            match; ``"or"`` requires at least one.  Defaults to ``"and"``.
        max_context_length: Maximum characters to extract from
            ``searchable_content`` as context.  Defaults to
            :data:`src.config.MAX_CONTEXT_LENGTH` (60).

    Returns:
        A list of result dicts, each with the keys:

        * ``"file"`` — the source file path (``str``)
        * ``"row_id"`` — the globally unique row ID (``str``)
        * ``"match_context"`` — truncated content snippet (``str``)
        * ``"keywords"`` — list of matched keyword tokens (``List[str]``)

        Results are sorted by the number of matched keywords (descending),
        then alphabetically by row ID for deterministic ordering.

    Raises:
        ValueError: If ``mode`` is not ``"and"`` or ``"or"``.
    """
    if mode not in ("and", "or"):
        raise ValueError(f"Invalid mode '{mode}'. Use 'and' or 'or'.")

    # Tokenize each raw keyword using the same pipeline as indexing.
    # Each raw keyword may produce zero or more normalized tokens.
    all_tokens: List[str] = []
    for kw in keywords:
        tokens = tokenize(kw)
        all_tokens.extend(tokens)

    if not all_tokens:
        logger.warning("No tokens produced from keywords: %r", keywords)
        return []

    # Build a set of unique tokens (preserving order) to look up.
    unique_tokens: List[str] = list(dict.fromkeys(all_tokens))

    logger.debug("Query tokens: %s (mode=%s)", unique_tokens, mode)

    # Collect candidate row IDs per token.
    token_hits: Dict[str, List[str]] = {}
    for token in unique_tokens:
        if token in index:
            token_hits[token] = index[token]
        else:
            token_hits[token] = []
            logger.debug("Token %r not found in index", token)

    # Count matches per row ID and track which tokens matched each row.
    match_counts: Dict[str, int] = {}
    row_tokens: Dict[str, List[str]] = {}
    for token, row_ids in token_hits.items():
        for rid in row_ids:
            match_counts[rid] = match_counts.get(rid, 0) + 1
            if rid not in row_tokens:
                row_tokens[rid] = []
            row_tokens[rid].append(token)

    # Filter based on mode.
    required_count: int = len(unique_tokens) if mode == "and" else 1
    matched_row_ids: List[tuple[str, int]] = []
    for rid, count in match_counts.items():
        if count >= required_count:
            matched_row_ids.append((rid, count))

    # Sort: descending by match count, then alphabetically by row ID.
    matched_row_ids.sort(key=lambda x: (-x[1], x[0]))

    # Build a lookup: row_id → (source_file, searchable_content).
    row_lookup: Dict[str, tuple[str, str]] = {}
    for df in dataframes:
        if "__row_id" not in df.columns:
            continue
        source_file: str = (
            str(df["__source_file"].iloc[0])
            if "__source_file" in df.columns
            else "unknown"
        )
        content_col: str = (
            "searchable_content"
            if "searchable_content" in df.columns
            else ""
        )
        for _, row in df.iterrows():
            rid: str = str(row["__row_id"])
            content: str = str(row[content_col]) if content_col else ""
            row_lookup[rid] = (source_file, content)

    # Build result dicts.
    results: List[Dict[str, Any]] = []
    for rid, _match_count in matched_row_ids:
        source_file, content = row_lookup.get(rid, ("unknown", ""))
        match_context: str = (
            content[:max_context_length] + "..."
            if len(content) > max_context_length
            else content
        )
        matched_keywords: List[str] = row_tokens.get(rid, [])

        results.append({
            "file": source_file,
            "row_id": rid,
            "match_context": match_context,
            "keywords": matched_keywords,
        })

    logger.info(
        "Query (mode=%s): %d result(s) from %d keyword(s)",
        mode,
        len(results),
        len(keywords),
    )
    return results


if __name__ == "__main__":
    # Simple self-test with a mock index and DataFrames.
    mock_index: Dict[str, List[str]] = {
        "\u5f20\u4e09": ["data/sample01.csv_1"],
        "\u6280\u672f\u90e8": ["data/sample01.csv_1", "data/sample01.csv_5"],
        "\u674e\u56db": ["data/sample01.csv_2"],
        "\u5e02\u573a\u90e8": ["data/sample02.csv_1"],
        "python": ["data/sample03.json_2"],
        "\u5929\u6c14": ["data/sample03.json_1"],
    }

    mock_dfs: List[pd.DataFrame] = [
        pd.DataFrame({
            "__row_id": [
                "data/sample01.csv_1",
                "data/sample01.csv_2",
                "data/sample01.csv_5",
            ],
            "__source_file": [
                "data/sample01.csv",
                "data/sample01.csv",
                "data/sample01.csv",
            ],
            "searchable_content": [
                "\u5f20\u4e09 \u6280\u672f\u90e8 \u5de5\u7a0b\u5e08 \u5317\u4eac",
                "\u674e\u56db \u5e02\u573a\u90e8 \u7ecf\u7406 \u4e0a\u6d77",
                "\u8d75\u516d \u6280\u672f\u90e8 \u5de5\u7a0b\u5e08 \u6df1\u5733",
            ],
        }),
        pd.DataFrame({
            "__row_id": ["data/sample03.json_1", "data/sample03.json_2"],
            "__source_file": ["data/sample03.json", "data/sample03.json"],
            "searchable_content": [
                "\u4eca\u5929\u5929\u6c14\u771f\u597d\uff0c\u9002\u5408\u51fa\u53bb\u6563\u6b65\u548c\u6652\u592a\u9633\u3002",
                "Python\u662f\u4e00\u95e8\u975e\u5e38\u4f18\u96c5\u7684\u7f16\u7a0b\u8bed\u8a00\uff0c\u5e7f\u6cdb\u5e94\u7528\u4e8e\u6570\u636e\u79d1\u5b66\u9886\u57df\u3002",
            ],
        }),
    ]

    print("=== AND mode: ['\u5f20\u4e09', '\u6280\u672f\u90e8'] ===")
    for r in execute_query(mock_index, mock_dfs, ["\u5f20\u4e09", "\u6280\u672f\u90e8"], mode="and"):
        print(f"  {r['file']} | {r['row_id']} | {r['keywords']}")
        print(f"    -> {r['match_context']}")

    print("\n=== OR mode: ['\u674e\u56db', '\u6280\u672f\u90e8'] ===")
    for r in execute_query(mock_index, mock_dfs, ["\u674e\u56db", "\u6280\u672f\u90e8"], mode="or"):
        print(f"  {r['file']} | {r['row_id']} | {r['keywords']}")
        print(f"    -> {r['match_context']}")

    print("\n=== Empty result: ['\u738b\u4e94'] ===")
    res = execute_query(mock_index, mock_dfs, ["\u738b\u4e94"], mode="and")
    print(f"  Results: {res}")

    print("\nAll self-tests completed.")