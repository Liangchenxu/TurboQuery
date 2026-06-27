import sys, os
os.chdir(r"d:\tqtq\TurboQuery")
sys.path.insert(0, r"d:\tqtq\TurboQuery")

results = []

# 1. config
try:
    from src.config import DEFAULT_INPUT, MAX_CONTEXT_LENGTH
    results.append("OK config")
except Exception as e:
    results.append(f"FAIL config: {e}")

# 2. logger
try:
    from src.logger import setup_logger
    results.append("OK logger")
except Exception as e:
    results.append(f"FAIL logger: {e}")

# 3. tokenizer
try:
    from src.tokenizer import tokenize
    results.append("OK tokenizer")
except Exception as e:
    results.append(f"FAIL tokenizer: {e}")

# 4. loader
try:
    from src.loader import load_files
    results.append("OK loader")
except Exception as e:
    results.append(f"FAIL loader: {e}")

# 5. cleaner
try:
    from src.cleaner import clean_dataframes
    results.append("OK cleaner")
except Exception as e:
    results.append(f"FAIL cleaner: {e}")

# 6. worker
try:
    from src.worker import process_file
    results.append("OK worker")
except Exception as e:
    results.append(f"FAIL worker: {e}")

# 7. merger
try:
    from src.merger import merge_indexes
    results.append("OK merger")
except Exception as e:
    results.append(f"FAIL merger: {e}")

# 8. indexer
try:
    from src.indexer import build_global_index
    results.append("OK indexer")
except Exception as e:
    results.append(f"FAIL indexer: {e}")

# 9. querier
try:
    from src.querier import execute_query
    results.append("OK querier")
except Exception as e:
    results.append(f"FAIL querier: {e}")

# 10. formatter
try:
    from src.formatter import format_terminal, format_json, format_csv
    results.append("OK formatter")
except Exception as e:
    results.append(f"FAIL formatter: {e}")

# 11. main
try:
    from src.main import main
    results.append("OK main")
except Exception as e:
    results.append(f"FAIL main: {e}")

with open(r"d:\tqtq\TurboQuery\_import_check.txt", "w", encoding="utf-8") as f:
    for r in results:
        f.write(r + "\n")
    f.write("\nDONE\n")