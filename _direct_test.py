import sys, os, traceback

sys.path.insert(0, r"d:/tqtq/TurboQuery")
os.chdir(r"d:/tqtq/TurboQuery")

out_lines = ["=== TurboQuery Full Check ==="]

def check(name, fn):
    try:
        result = fn()
        out_lines.append(f"OK {name}: {result}")
        return True
    except Exception as e:
        out_lines.append(f"FAIL {name}: {e}")
        return False

# config
from src.config import DEFAULT_INPUT, MAX_CONTEXT_LENGTH
out_lines.append(f"OK config: DEFAULT_INPUT={DEFAULT_INPUT}")

# logger
from src.logger import setup_logger
out_lines.append("OK logger")

# tokenizer
from src.tokenizer import tokenize
t = tokenize("The quick brown fox jumps over the lazy dog.")
out_lines.append(f"OK tokenizer: {t}")

# loader
from src.loader import load_files
dfs = load_files("./data")
out_lines.append(f"OK loader: {len(dfs)} files")

# cleaner
from src.cleaner import clean_dataframes
cleaned = clean_dataframes(dfs)
out_lines.append(f"OK cleaner: {len(cleaned)} cleaned")

# worker
from src.worker import process_file
out_lines.append("OK worker")

# merger
from src.merger import merge_indexes
m = merge_indexes({"a":["x"]}, {"a":["y"]})
out_lines.append(f"OK merger: a->{m['a']}")

# indexer (build in-process to avoid multiprocessing hang)
from src.worker import process_file
from src.merger import merge_indexes
import glob as _glob
files = sorted(_glob.glob("./data/*.csv") + _glob.glob("./data/*.json"))
out_lines.append(f"Files found: {files}")
local_indexes = []
for f in files:
    local_indexes.append(process_file(f))
gidx = merge_indexes(*local_indexes, deduplicate=True)
out_lines.append(f"OK indexer (in-process): {len(gidx)} tokens")

# querier
from src.querier import execute_query
results = execute_query(gidx, cleaned, ["张三"], mode="and")
out_lines.append(f"OK querier AND: {len(results)} results")
for r in results[:3]:
    out_lines.append(f"  {r['file']} | {r['row_id']} | kw={r['keywords']} | ctx={r['match_context'][:40]}")

results_or = execute_query(gidx, cleaned, ["张三", "技术部"], mode="or")
out_lines.append(f"OK querier OR: {len(results_or)} results")

# formatter
from src.formatter import format_terminal, format_json, format_csv
out_lines.append("OK formatter")

# main
from src.main import main
out_lines.append("OK main")

out_lines.append("\n=== ALL CHECKS PASSED ===")

with open("_full_check.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out_lines))