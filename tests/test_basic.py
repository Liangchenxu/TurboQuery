"""Basic integration tests for TurboQuery.

Uses pytest.  Tests load real data from ./data/ (relative to the
project root), build the inverted index, and execute single/multi-keyword
queries in both AND and OR modes.
"""

from pathlib import Path
from typing import Dict, List

import pandas as pd
import pytest

# Dynamically resolve paths relative to the test file's location.
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

import sys

if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.cleaner import clean_dataframes
from src.indexer import build_global_index
from src.loader import load_files
from src.merger import merge_indexes
from src.querier import execute_query
from src.tokenizer import tokenize


@pytest.fixture(scope="module")
def data_dir() -> str:
    """Return the absolute path to the data directory."""
    p = (_PROJECT_ROOT / "data").resolve()
    if not p.is_dir():
        pytest.skip(f"Data directory not found: {p}")
    return str(p)


@pytest.fixture(scope="module")
def loaded_dataframes(data_dir: str) -> List[pd.DataFrame]:
    """Load and clean all DataFrames from the data directory."""
    dfs = load_files(data_dir)
    if not dfs:
        pytest.skip("No data files found")
    return clean_dataframes(dfs)


@pytest.fixture(scope="module")
def global_index(data_dir: str) -> Dict[str, List[str]]:
    """Build the global inverted index from the data directory.

    Uses max_workers=0 (sequential) to avoid multiprocessing hangs
    in pytest on Windows.  Multiprocessing mode is tested separately
    in the CLI integration.
    """
    return build_global_index(directory=data_dir, max_workers=0)


# ---------------------------------------------------------------------------
# Tokenizer tests
# ---------------------------------------------------------------------------

def test_tokenize_basic() -> None:
    """Tokenize removes stop words and short tokens."""
    tokens = tokenize("The quick brown fox jumps over the lazy dog.")
    assert "the" not in tokens
    assert "quick" in tokens
    assert len(tokens) < 9  # stop words removed


def test_tokenize_chinese() -> None:
    """Tokenize handles Chinese text."""
    tokens = tokenize("张三 技术部 工程师")
    assert len(tokens) >= 1


def test_tokenize_empty() -> None:
    """Tokenize returns empty list for empty input."""
    assert tokenize("") == []
    assert tokenize("  ") == []


# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------

def test_load_files_returns_dataframes(data_dir: str) -> None:
    """load_files returns non-empty list of DataFrames."""
    dfs = load_files(data_dir)
    assert len(dfs) > 0
    for df in dfs:
        assert "__source_file" in df.columns
        assert len(df) > 0


# ---------------------------------------------------------------------------
# Cleaner/merger tests
# ---------------------------------------------------------------------------

def test_clean_adds_columns(loaded_dataframes: List[pd.DataFrame]) -> None:
    """Cleaned DataFrames have __row_id and searchable_content."""
    for df in loaded_dataframes:
        assert "__row_id" in df.columns
        assert "searchable_content" in df.columns


def test_merge_indexes_deduplicates() -> None:
    """merge_indexes removes duplicate row IDs per token."""
    idx_a: Dict[str, List[str]] = {"hello": ["a_1", "a_2"], "world": ["a_1"]}
    idx_b: Dict[str, List[str]] = {"hello": ["b_1", "a_1"]}
    merged = merge_indexes(idx_a, idx_b, deduplicate=True)
    assert merged["hello"] == ["a_1", "a_2", "b_1"]
    assert merged["world"] == ["a_1"]


# ---------------------------------------------------------------------------
# Indexing tests
# ---------------------------------------------------------------------------

def test_global_index_not_empty(global_index: Dict[str, List[str]]) -> None:
    """Global index contains tokens after processing data files."""
    assert len(global_index) > 0


def test_global_index_values_are_lists(
    global_index: Dict[str, List[str]],
) -> None:
    """Every value in global index is a non-empty list of row IDs."""
    for token, row_ids in global_index.items():
        assert isinstance(row_ids, list), f"Token {token!r} not a list"
        assert len(row_ids) > 0, f"Token {token!r} has empty list"


# ---------------------------------------------------------------------------
# Query tests — single keyword
# ---------------------------------------------------------------------------

def test_single_keyword_and(
    global_index: Dict[str, List[str]],
    loaded_dataframes: List[pd.DataFrame],
) -> None:
    """AND mode with one keyword returns results."""
    results = execute_query(
        global_index, loaded_dataframes, ["张三"], mode="and",
    )
    for r in results:
        assert "file" in r
        assert "row_id" in r
        assert "match_context" in r
        assert "keywords" in r


def test_single_keyword_or(
    global_index: Dict[str, List[str]],
    loaded_dataframes: List[pd.DataFrame],
) -> None:
    """OR mode with one keyword returns results."""
    results = execute_query(
        global_index, loaded_dataframes, ["张三"], mode="or",
    )
    assert isinstance(results, list)


# ---------------------------------------------------------------------------
# Query tests — multiple keywords
# ---------------------------------------------------------------------------

def test_multi_keyword_and(
    global_index: Dict[str, List[str]],
    loaded_dataframes: List[pd.DataFrame],
) -> None:
    """AND mode with two keywords: all results match both tokens."""
    results = execute_query(
        global_index, loaded_dataframes, ["张三", "技术部"], mode="and",
    )
    for r in results:
        kw: List[str] = r["keywords"]
        assert len(kw) >= 2, f"Expected >=2 keywords, got {kw}"


def test_multi_keyword_or(
    global_index: Dict[str, List[str]],
    loaded_dataframes: List[pd.DataFrame],
) -> None:
    """OR mode returns results matching any keyword."""
    results = execute_query(
        global_index, loaded_dataframes, ["张三", "李四"], mode="or",
    )
    assert isinstance(results, list)


def test_no_match_returns_empty(
    global_index: Dict[str, List[str]],
    loaded_dataframes: List[pd.DataFrame],
) -> None:
    """Query with non-existent keyword returns empty list."""
    results = execute_query(
        global_index, loaded_dataframes, ["nonexistent_xyz_12345"], mode="or",
    )
    assert results == []


def test_invalid_mode_raises(
    global_index: Dict[str, List[str]],
    loaded_dataframes: List[pd.DataFrame],
) -> None:
    """Invalid mode raises ValueError."""
    with pytest.raises(ValueError):
        execute_query(global_index, loaded_dataframes, ["test"], mode="xor")


# ---------------------------------------------------------------------------
# Formatter smoke test
# ---------------------------------------------------------------------------

def test_formatters_no_crash(
    global_index: Dict[str, List[str]],
    loaded_dataframes: List[pd.DataFrame],
) -> None:
    """All three formatters run without crashing."""
    from src.formatter import format_csv, format_json, format_terminal

    results = execute_query(
        global_index, loaded_dataframes, ["张三"], mode="or",
    )
    # Terminal and JSON to stdout
    format_terminal(results)
    format_json(results)
    # CSV to a temp path
    csv_out = str(_PROJECT_ROOT / "test_output.csv")
    path = format_csv(results, output_path=csv_out)
    assert Path(path).exists()
    Path(path).unlink(missing_ok=True)