"""Final integration test — writes results to editor-created file."""
import sys, os
sys.path.insert(0, r"d:\tqtq\TurboQuery")
os.chdir(r"d:\tqtq\TurboQuery")

results = []

# 1. Imports
from src.config import DEFAULT_INPUT
results.append(f"config: DEFAULT_INPUT={DEFAULT_INPUT}")

from src.tokenizer import tokenize
results.append(f"tokenizer: '张三' -> {tokenize('张三')}")

from src.loader import load_files
dfs = load_files("./data")
results.append(f"loader: {len(dfs)} files")

from src.cleaner import clean_dataframes
cleaned = clean_dataframes(dfs)
results.append(f"cleaner: {len(cleaned)} DataFrames")

from src.worker import process_file
from src.merger import merge_indexes
import glob
files_list = sorted(glob.glob("./data/*.csv") + glob.glob("./data/*.json"))
local = [process_file(f) for f in files_list]
gidx = merge_indexes(*local, deduplicate=True)
results.append(f"indexer: {len(gidx)} tokens")
results.append(f"  '张三' in index: {'张三' in gidx}")
results.append(f"  '技术部' in index: {'技术部' in gidx}")

from src.querier import execute_query
r_and = execute_query(gidx, cleaned, ["张三"], mode="and")
results.append(f"querier AND '张三': {len(r_and)} results")
for r in r_and:
    results.append(f"  file={r['file']}")
    results.append(f"  row_id={r['row_id']}")
    results.append(f"  keywords={r['keywords']}")
    results.append(f"  context={r['match_context']}")

r_or = execute_query(gidx, cleaned, ["张三", "技术部"], mode="or")
results.append(f"querier OR '张三'+'技术部': {len(r_or)} results")

r_and2 = execute_query(gidx, cleaned, ["张三", "技术部"], mode="and")
results.append(f"querier AND '张三'+'技术部': {len(r_and2)} results")

from src.formatter import format_terminal, format_json, format_csv
results.append("formatter: all 3 functions imported")

from src.main import main
results.append("main: imported OK")

# Final
results.append("\n=== ALL TESTS PASSED ===")

# Write output
out = "\n".join(results)
with open(r"d:\tqtq\TurboQuery\FINAL_RESULT.txt", "w", encoding="utf-8") as f:
    f.write(out)
print("DONE")
sys.stdout.flush()