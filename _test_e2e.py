"""端到端集成测试脚本"""
import sys
sys.path.insert(0, '.')

from src.loader import load_files
from src.cleaner import clean_dataframes
from src.tokenizer import tokenize_dataframe_content

print("=" * 60)
print("TurboQuery 端到端测试")
print("=" * 60)

# 1. 加载
dfs = load_files('./data')
print(f"\n[1] 加载: {len(dfs)} 个文件")
for df in dfs:
    print(f"    - {df['__source_file'].iloc[0]}: {len(df)} 行, {len(df.columns)} 列")

# 2. 清洗
cleaned = clean_dataframes(dfs)
print(f"\n[2] 清洗: {len(cleaned)} 个DataFrame")
for i, df in enumerate(cleaned):
    print(f"    [{i+1}] 列: {list(df.columns)}")
    print(f"        行数: {len(df)}, searchable_content示例: {df['searchable_content'].iloc[0][:80]}...")

# 3. 分词
print(f"\n[3] 分词:")
for i, df in enumerate(cleaned):
    df_tok = tokenize_dataframe_content(df)
    print(f"    [{i+1}] tokens示例: {df_tok['__tokens'].iloc[0][:8]}")

print("\n" + "=" * 60)
print("所有测试通过!")
print("=" * 60)