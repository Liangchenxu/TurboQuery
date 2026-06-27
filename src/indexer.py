"""Parallel index orchestration module for TurboQuery.

Uses ``multiprocessing.Pool`` to process multiple data files concurrently
via ``worker.process_file``, then merges all local inverted indexes into
a single global inverted index.  The number of worker processes is
determined dynamically from ``os.cpu_count()``.
"""

import multiprocessing
import os
from pathlib import Path
from typing import Dict, List, Optional

from src.config import DEFAULT_INPUT
from src.logger import setup_logger
from src.merger import merge_indexes
from src.worker import process_file

logger = setup_logger(name="indexer")


def _collect_files(directory: str) -> List[str]:
    """Collect all supported data files from a directory.

    Args:
        directory: Path to the directory to scan.

    Returns:
        A sorted list of absolute file paths for .csv and .json files.

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    dir_path = Path(directory).resolve()
    if not dir_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    supported = {".csv", ".json"}
    files: List[str] = []
    for entry in sorted(dir_path.iterdir()):
        if entry.is_file() and entry.suffix.lower() in supported:
            files.append(str(entry.resolve()))
    return files


def build_global_index(
    directory: str = DEFAULT_INPUT,
    max_workers: Optional[int] = None,
    verbose: bool = False,
) -> Dict[str, List[str]]:
    """Build a global inverted index from all data files in a directory.

    Each file is processed in parallel using ``multiprocessing.Pool``.
    The local inverted indexes returned by each worker are merged via
    :func:`src.merger.merge_indexes` into a single dictionary mapping
    tokens to the union of all matching row IDs (deduplicated).

    Args:
        directory: Path to the directory containing data files.
            Defaults to ``DEFAULT_INPUT`` (``"./data"``).
        max_workers: Maximum number of worker processes.  Defaults to
            ``os.cpu_count()`` when None is provided.
        verbose: If True, enable DEBUG-level logging.

    Returns:
        A global inverted index: ``{token: [row_id, ...]}``.  Row IDs
        are globally unique (format ``"{filepath}_{row_number}"``).

    Raises:
        FileNotFoundError: If the directory does not exist.
    """
    if verbose:
        logger.setLevel("DEBUG")

    files = _collect_files(directory)
    if not files:
        logger.warning("No supported files found in %s", directory)
        return {}

    # Determine worker count dynamically from CPU cores.
    if max_workers is None:
        max_workers = os.cpu_count() or 4
    # max_workers=0 means sequential processing (no Pool).
    # Clamp to the number of files.
    if max_workers > 0:
        max_workers = min(max_workers, len(files))

    use_pool: bool = max_workers > 1

    logger.info(
        "Building global index from %d file(s) with %d worker(s) [cpu_count=%d, pool=%s]",
        len(files),
        max_workers if use_pool else 1,
        os.cpu_count() or 0,
        use_pool,
    )

    if use_pool:
        # Use multiprocessing.Pool for CPU-bound parallelism.
        # On Windows, the caller MUST invoke this from a ``__main__``
        # guard.  When called from pytest or other non-main contexts,
        # set ``max_workers=0`` to avoid hangs.
        with multiprocessing.Pool(processes=max_workers) as pool:
            local_indexes: List[Dict[str, List[str]]] = pool.map(
                process_file, files
            )
    else:
        # Sequential fallback — safe in all contexts.
        local_indexes = [process_file(f) for f in files]

    # Merge all local indexes into one global index (deduplicates row
    # IDs per token).
    global_index: Dict[str, List[str]] = merge_indexes(
        *local_indexes, deduplicate=True
    )

    logger.info(
        "Global index built: %d unique tokens across %d file(s)",
        len(global_index),
        len(files),
    )
    return global_index


if __name__ == "__main__":
    # Simple self-test: build index from ./data/ and show stats.
    import sys

    test_dir = "./data"
    workers: Optional[int] = None
    if len(sys.argv) > 1:
        test_dir = sys.argv[1]
    if len(sys.argv) > 2:
        workers = int(sys.argv[2])

    print(f"Building global index from: {test_dir} (workers={workers})")
    gindex = build_global_index(test_dir, max_workers=workers, verbose=True)
    print(f"  Unique tokens: {len(gindex)}")
    # Show a few sample entries.
    count = 0
    for token, row_ids in sorted(gindex.items()):
        if count >= 10:
            break
        print(
            f"  {token!r}: {len(row_ids)} row(s) — "
            f"{row_ids[:3]}{'...' if len(row_ids) > 3 else ''}"
        )
        count += 1
    if not gindex:
        print("  (empty index)")