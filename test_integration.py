"""Integration test script for TurboQuery pipeline."""
import sys
sys.path.insert(0, '.')

from src.loader import load_directory
from src.cleaner import clean_dataframes
from src.tokenizer import tokenize_batch

def main():
    dfs = load_directory('./data')
    print(f'加载了 {len(dfs)} 个 DataFrame')

    cleaned = clean_dataframes(dfs)
    print(f'清洗后 {len(cleaned)} 个 DataFrame')

    for df in cleaned:
        source = df['__source_file'].iloc[0]
        print(f'  {source}: {len(df)} 行, 列: {list(df.columns)}')

        tokens = tokenize_batch(df['searchable_content'].tolist())
        print(f'  分词结果示例: {tokens[0][:5]}')

if __name__ == '__main__':
    main()