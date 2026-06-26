"""Text tokenization module for TurboQuery.

Extracts tokens from text using a regular expression, normalizes to
lowercase, filters short tokens, and removes common English stop words.
"""

import re
from typing import List

from src.logger import setup_logger

logger = setup_logger(name="tokenizer")

# 50 common English stop words.
_STOP_WORDS: set[str] = {
    "the", "be", "to", "of", "and", "a", "in", "that", "have", "i",
    "it", "for", "not", "on", "with", "he", "as", "you", "do", "at",
    "this", "but", "his", "by", "from", "they", "we", "say", "her", "she",
    "or", "an", "will", "my", "one", "all", "would", "there", "their",
    "what", "so", "up", "out", "if", "about", "who", "get", "which", "go",
    "me", "when", "make", "can", "like", "time", "no", "just", "him", "know",
}

# Pre-compiled regex for word extraction: matches one or more word characters.
_WORD_PATTERN: re.Pattern = re.compile(r"\w+", re.UNICODE)


def tokenize(text: str) -> List[str]:
    """Tokenize a text string into a list of normalized word tokens.

    Processing steps:

    1. Extract all word tokens using the regex ``\\w+`` (Unicode-aware).
    2. Convert every token to lowercase.
    3. Discard tokens whose length is 2 characters or fewer.
    4. Remove tokens that appear in the 50-word English stop list.

    Args:
        text: The raw input text to tokenize.  An empty string is
            handled gracefully and returns an empty list.

    Returns:
        A list of lowercase word tokens with short tokens and stop
        words removed.  The order of tokens is preserved from the
        original text.

    Example:
        >>> tokenize("The quick brown fox jumps over the lazy dog.")
        ['quick', 'brown', 'fox', 'jumps', 'over', 'lazy', 'dog']
    """
    if not text or not isinstance(text, str):
        logger.debug("tokenize received empty or non-string input, returning []")
        return []

    # Step 1: extract words.
    raw_tokens: List[str] = _WORD_PATTERN.findall(text)

    # Step 2: lowercase.
    lowered = [t.lower() for t in raw_tokens]

    # Step 3: filter by length > 2.
    length_filtered = [t for t in lowered if len(t) > 2]

    # Step 4: remove stop words.
    result = [t for t in length_filtered if t not in _STOP_WORDS]

    logger.debug("Tokenized text (%d chars) → %d tokens", len(text), len(result))
    return result


def tokenize_dataframe_column(
    df: "pd.DataFrame",  # noqa: F821
    column: str = "searchable_content",
) -> "pd.Series":  # noqa: F821
    """Apply tokenization to every row of a DataFrame column.

    Args:
        df: A pandas DataFrame.
        column: Name of the column to tokenize.  Defaults to
            ``"searchable_content"``.

    Returns:
        A pandas Series where each element is a list of tokens.
    """
    import pandas as pd

    logger.info("Tokenizing column '%s' across %d rows", column, len(df))
    return df[column].apply(tokenize)


if __name__ == "__main__":
    # Simple self-test: tokenize a few sample strings.
    samples = [
        "The quick brown fox jumps over the lazy dog.",
        "Hello, world! This is a test of the TurboQuery tokenizer.",
        "AI and ML are transforming data engineering at scale.",
        "",  # empty string
        "a an the it is of in on at to be we he she they",  # all stop/short
        "Python 3.10+ pandas DataFrame 数据 查询 工具",  # mixed Chinese/English
    ]

    print("=== Tokenizer Self-Test ===")
    for s in samples:
        tokens = tokenize(s)
        print(f"  Input : {s!r}")
        print(f"  Tokens: {tokens}")
        print()