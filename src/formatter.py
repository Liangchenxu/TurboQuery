"""Result formatting module for TurboQuery.

Provides three output formats for query results:

* ``terminal`` — color-highlighted terminal output (requires ``colorama``).
* ``json``   — one JSON object per line written to stdout or a file.
* ``csv``    — CSV file written to the current working directory (``./``).
"""

import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.logger import setup_logger

logger = setup_logger(name="formatter")

# ---------------------------------------------------------------------------
# Terminal / colorama helpers
# ---------------------------------------------------------------------------

try:
    import colorama
    from colorama import Fore, Style

    colorama.init(autoreset=True)
    _COLORAMA_AVAILABLE: bool = True
except ImportError:
    _COLORAMA_AVAILABLE = False

    class _NoopFore:  # type: ignore[no-redef]
        def __getattr__(self, _name: str) -> str:
            return ""

    class _NoopStyle:  # type: ignore[no-redef]
        def __getattr__(self, _name: str) -> str:
            return ""

    Fore = _NoopFore()  # type: ignore[misc]
    Style = _NoopStyle()  # type: ignore[misc]

# Color palette for terminal output.
_COLOR_MAP: Dict[str, str] = {
    "file": Fore.CYAN if _COLORAMA_AVAILABLE else "",
    "row_id": Fore.GREEN if _COLORAMA_AVAILABLE else "",
    "context": Fore.YELLOW if _COLORAMA_AVAILABLE else "",
    "keywords": Fore.MAGENTA if _COLORAMA_AVAILABLE else "",
    "reset": Style.RESET_ALL if _COLORAMA_AVAILABLE else "",
}


def _highlight_keywords(text: str, keywords: List[str]) -> str:
    """Wrap matched keywords in ANSI color codes within *text*."""
    if not _COLORAMA_AVAILABLE or not keywords:
        return text
    for kw in sorted(set(keywords), key=len, reverse=True):
        if kw:
            text = text.replace(kw, f"{Fore.RED}{kw}{Style.RESET_ALL}")
    return text


# ---------------------------------------------------------------------------
# Public formatters
# ---------------------------------------------------------------------------

def format_terminal(
    results: List[Dict[str, Any]],
    *,
    file: Optional[str] = None,
) -> None:
    """Write query results as color-highlighted text to stdout or a file."""
    if not results:
        msg = "No results found.\n"
        if file:
            Path(file).write_text(msg, encoding="utf-8")
        else:
            sys.stdout.write(msg)
        return

    use_color: bool = _COLORAMA_AVAILABLE and file is None
    c = _COLOR_MAP

    lines: List[str] = []
    lines.append(f"Found {len(results)} result(s):")
    lines.append("-" * 60)

    for rank, result in enumerate(results, start=1):
        file_path: str = result.get("file", "unknown")
        row_id: str = result.get("row_id", "?")
        context: str = result.get("match_context", "")
        keywords: List[str] = result.get("keywords", [])

        if use_color:
            ctx_display = _highlight_keywords(context, keywords)
            lines.append(
                f"#{rank}  {c['file']}file={file_path}{c['reset']}  "
                f"{c['row_id']}row_id={row_id}{c['reset']}"
            )
            lines.append(
                f"      {c['keywords']}keywords=[{', '.join(keywords)}]"
                f"{c['reset']}"
            )
            lines.append(f"      {c['context']}{ctx_display}{c['reset']}")
        else:
            lines.append(f"#{rank}  file={file_path}  row_id={row_id}")
            lines.append(f"      keywords=[{', '.join(keywords)}]")
            lines.append(f"      {context}")
        lines.append("")

    output = "\n".join(lines) + "\n"

    if file:
        Path(file).write_text(output, encoding="utf-8")
        logger.info("Terminal output written to %s", file)
    else:
        sys.stdout.write(output)


def format_json(
    results: List[Dict[str, Any]],
    *,
    file: Optional[str] = None,
) -> None:
    """Write query results as one JSON object per line."""
    if not results:
        msg = json.dumps({"info": "No results found."}, ensure_ascii=False) + "\n"
        if file:
            Path(file).write_text(msg, encoding="utf-8")
        else:
            sys.stdout.write(msg)
        return

    lines_out: List[str] = []
    for result in results:
        lines_out.append(json.dumps(result, ensure_ascii=False))
    output = "\n".join(lines_out) + "\n"

    if file:
        Path(file).write_text(output, encoding="utf-8")
        logger.info("JSON output written to %s", file)
    else:
        sys.stdout.write(output)


def format_csv(
    results: List[Dict[str, Any]],
    *,
    output_path: Optional[str] = None,
) -> str:
    """Write query results as a CSV file to the current working directory.

    Returns the absolute path to the written file.
    """
    if output_path is None:
        output_path = str(Path("./query_results.csv").resolve())
    else:
        output_path = str(Path(output_path).resolve())

    fieldnames: List[str] = ["file", "row_id", "match_context", "keywords"]

    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()

        if not results:
            writer.writerow({
                "file": "N/A",
                "row_id": "N/A",
                "match_context": "No results found.",
                "keywords": "[]",
            })
        else:
            for result in results:
                writer.writerow({
                    "file": result.get("file", ""),
                    "row_id": result.get("row_id", ""),
                    "match_context": result.get("match_context", ""),
                    "keywords": json.dumps(
                        result.get("keywords", []), ensure_ascii=False
                    ),
                })

    logger.info("CSV output written to %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mock_results: List[Dict[str, Any]] = [
        {
            "file": "data/sample01.csv",
            "row_id": "data/sample01.csv_1",
            "match_context": "\u5f20\u4e09 \u6280\u672f\u90e8 \u5de5\u7a0b\u5e08 \u5317\u4eac",
            "keywords": ["\u5f20\u4e09", "\u6280\u672f\u90e8"],
        },
        {
            "file": "data/sample01.csv",
            "row_id": "data/sample01.csv_5",
            "match_context": "\u8d75\u516d \u6280\u672f\u90e8 \u5de5\u7a0b\u5e08 \u6df1\u5733",
            "keywords": ["\u6280\u672f\u90e8"],
        },
        {
            "file": "data/sample03.json",
            "row_id": "data/sample03.json_2",
            "match_context": "Python\u662f\u4e00\u95e8\u975e\u5e38\u4f18\u96c5\u7684\u7f16\u7a0b\u8bed\u8a00\uff0c\u5e7f\u6cdb\u5e94\u7528\u4e8e\u6570\u636e\u79d1\u5b66\u9886\u57df\u3002",
            "keywords": ["python"],
        },
    ]

    print("=== Terminal output ===")
    format_terminal(mock_results)

    print("\n=== JSON output ===")
    format_json(mock_results)

    print("\n=== CSV output ===")
    csv_path = format_csv(mock_results)
    print(f"CSV written to: {csv_path}")

    print("\n=== Empty results ===")
    format_terminal([])
    format_json([])
    csv_empty = format_csv([], output_path="./empty_results.csv")
    print(f"Empty CSV written to: {csv_empty}")