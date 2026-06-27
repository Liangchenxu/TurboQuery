# TurboQuery

**Inverted-index-powered keyword search over CSV/JSON files.**

TurboQuery scans a directory of `.csv` and `.json` files, builds a
global inverted index using multiprocessing, then lets you query the
data with space-separated keywords in AND or OR mode. Results are
returned with context snippets and can be formatted as colour-highlighted
terminal output, one-JSON-per-line, or CSV.

---

## Features

- **Multi-format input** — reads `.csv` (auto-detects UTF-8/GBK encoding)
  and `.json` (array-of-objects or single object).
- **Column normalisation** — column names are lowercased and underscored;
  all text columns are merged into a single `searchable_content` field.
- **Inverted index** — built with `multiprocessing.Pool` using
  CPU-count-determined workers for fast parallel indexing.
- **Flexible query modes** — AND (all keywords must match) or OR (any
  keyword matches). Results ranked by match count.
- **Three output formats** — terminal (colour via `colorama`), JSON
  (one object per line), CSV (written to `./query_results.csv`).
- **Full type annotations** — Python 3.10+ typing throughout.
- **No hard-coded absolute paths** — everything uses relative or
  dynamically-resolved paths.

---

## Installation

```bash
# 1. Clone the repository
git clone <repo-url>
cd TurboQuery

# 2. (Optional) Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # macOS / Linux

# 3. Install dependencies
pip install pandas colorama pytest
```

---

## Quick Start

### 1. Prepare your data

Drop `.csv` or `.json` files into the `./data/` directory. Example:

```csv
姓名,部门,工号,入职日期
张三,技术部,TQ001,2020-03-15
李四,市场部,TQ002,2019-07-22
```

```json
[{"id": 1, "content": "今天天气真好。", "date": "2023-01-15"}]
```

### 2. Run a query

```bash
# Terminal output (default) — AND mode
python -m src.main --input ./data --query "张三 技术部"

# JSON output, OR mode
python -m src.main --input ./data --query "张三 技术部" --mode or --format json

# CSV output to a custom file
python -m src.main --input ./data --query "技术部" --format csv --output ./results.csv

# Debug logging
python -m src.main --input ./data --query "张三" --verbose
```

---

## CLI Reference

| Argument     | Required | Default      | Description                                      |
|-------------|----------|--------------|--------------------------------------------------|
| `--input`   | **yes**  | —            | Directory containing `.csv` / `.json` files       |
| `--query`   | **yes**  | —            | Space-separated keywords (e.g. `"张三 技术部"`)   |
| `--mode`    | no       | `and`        | `and` \| `or`                                     |
| `--format`  | no       | `terminal`   | `terminal` \| `json` \| `csv`                     |
| `--output`  | no       | `stdout` / `./query_results.csv` | Output file path          |
| `--verbose` | no       | off          | Enable DEBUG-level logging                       |

**Exit codes:** 0 = success, non-zero = error (1=empty query, 2=dir not
found, 3=load error, 4=no files, 5=clean error, 6=index error, 7=query
error, 8=unexpected query error, 9=unknown format, 10=output error).

---

## Module Overview

```
src/
├── config.py       # DEFAULT_INPUT, MAX_CONTEXT_LENGTH
├── logger.py       # Unified logging setup
├── loader.py       # File scanner & parser (CSV/JSON, encoding detection)
├── cleaner.py      # Normalise columns, fill NA, build searchable_content
├── tokenizer.py    # Regex-based tokeniser with stop-word removal
├── worker.py       # Single-file pipeline: load→clean→tokenize→local index
├── indexer.py      # Multiprocessing Pool dispatcher for parallel indexing
├── merger.py       # Merge & deduplicate local inverted indexes
├── querier.py      # Query executor (AND/OR, context extraction)
├── formatter.py    # terminal / json / csv output formatters
└── main.py         # CLI entry point (argparse)
```

---

## Architecture

```
                           ┌──────────┐
                           │  main.py │  CLI entry
                           └────┬─────┘
                                │
               ┌────────────────┼────────────────┐
               ▼                ▼                ▼
        ┌──────────┐    ┌───────────┐    ┌───────────┐
        │ loader.py│    │indexer.py │    │ querier.py │
        │ +cleaner │    │(Pool.map) │    │(AND/OR)   │
        └────┬─────┘    └─────┬─────┘    └─────┬─────┘
             │                │                │
             └──── worker.py◄─┘                │
                    (per file)                 │
                                               ▼
                    ┌───────────┐     ┌───────────────┐
                    │ merger.py │     │ formatter.py   │
                    │(dedup)    │     │term/json/csv   │
                    └───────────┘     └───────────────┘
```

---

## Running Tests

```bash
# Run all tests from the project root
pytest tests/ -v

# Run a specific test file
pytest tests/test_basic.py -v

# With coverage (if installed)
pytest tests/ --cov=src --cov-report=term-missing
```

---

## Dependencies

- **Python 3.10+**
- `pandas` — DataFrame handling
- `colorama` (optional) — coloured terminal output
- `pytest` (dev) — test runner

---

## License

MIT