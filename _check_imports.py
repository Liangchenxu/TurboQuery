"""Quick import check."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import re

errors = []

try:
    from src.config import DEFAULT_INPUT, MAX_CONTEXT_LENGTH
    print(f"[OK] config: DEFAULT_INPUT={DEFAULT_INPUT}, MAX_CONTEXT_LENGTH={MAX_CONTEXT_LENGTH}")
except Exception as e:
    errors.append(f"config: {e}")

try:
    from src.logger import setup_logger
    print("[OK] logger")
except Exception as e:
    errors.append(f"logger: {e}")

try:
    from src.loader import load_files
    print("[OK] loader")
except Exception as e:
    errors.append(f"loader: {e}")

try:
    from src.cleaner import clean_dataframes
    print("[OK] cleaner")
except Exception as e:
    errors.append(f"cleaner: {e}")

try:
    from src.tokenizer import tokenize
    print("[OK] tokenizer")
except Exception as e:
    errors.append(f"tokenizer: {e}")

try:
    from src.worker import process_file
    print("[OK] worker")
except Exception as e:
    errors.append(f"worker: {e}")

try:
    from src.indexer import build_global_index
    print("[OK] indexer")
except Exception as e:
    errors.append(f"indexer: {e}")

try:
    from src.merger import merge_indexes
    print("[OK] merger")
except Exception as e:
    errors.append(f"merger: {e}")

try:
    from src.querier import execute_query
    print("[OK] querier")
except Exception as e:
    errors.append(f"querier: {e}")

try:
    from src.formatter import format_terminal, format_json, format_csv
    print("[OK] formatter")
except Exception as e:
    errors.append(f"formatter: {e}")

try:
    from src.main import main
    print("[OK] main")
except Exception as e:
    errors.append(f"main: {e}")

# Try a real load
try:
    dfs = load_files("./data")
    print(f"[OK] load_files: {len(dfs)} file(s)")
    cleaned = clean_dataframes(dfs)
    print(f"[OK] clean_dataframes: {len(cleaned)} cleaned")
except Exception as e:
    errors.append(f"load/clean: {e}")

# Try index + query
try:
    idx = build_global_index("./data", max_workers=2)
    print(f"[OK] build_global_index: {len(idx)} tokens")
    results = execute_query(idx, cleaned, ["张三"], mode="and")
    print(f"[OK] execute_query AND: {len(results)} result(s)")
    results_or = execute_query(idx, cleaned, ["张三", "技术部"], mode="or")
    print(f"[OK] execute_query OR: {len(results_or)} result(s)")
except Exception as e:
    errors.append(f"index/query: {e}")

if errors:
    print(f"\n{len(errors)} ERROR(S):")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\nAll checks PASSED.")