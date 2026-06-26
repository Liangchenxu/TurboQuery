"""Quick integration test for loader module."""
from src.loader import load_files

dfs = load_files("./data")
print(f"Loaded {len(dfs)} DataFrames")
for df in dfs:
    src = df["__source_file"].iloc[0]
    print(f"  Shape: {df.shape}, Source: {src}")
    print(f"  Columns: {list(df.columns)}")
    print()