import math
import re
from typing import Dict, List

def tokenize(text: str) -> List[str]:
    """Simple alphanumeric tokenizer and lowercaser."""
    return re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text.lower())

def score_text_bm25(query_tokens: List[str], doc_tokens: List[str], avg_dl: float = 100.0, k1: float = 1.5, b: float = 0.75) -> float:
    """Compute BM25-like lexical relevance score between query tokens and document tokens."""
    if not doc_tokens or not query_tokens:
        return 0.0
    doc_len = len(doc_tokens)
    tf: Dict[str, int] = {}
    for t in doc_tokens:
        tf[t] = tf.get(t, 0) + 1

    score = 0.0
    for q in query_tokens:
        freq = tf.get(q, 0)
        if freq > 0:
            numerator = freq * (k1 + 1.0)
            denominator = freq + k1 * (1.0 - b + b * (doc_len / avg_dl))
            score += (numerator / denominator)
    return score
