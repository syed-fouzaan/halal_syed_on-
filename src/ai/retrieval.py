from typing import Any, Dict, List
from src.ai.embeddings import tokenize, score_text_bm25

def retrieve_top_chunks(query: str, evidence_chunks: List[Dict[str, Any]], top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Query normalization and relevance retrieval for evidence chunks.
    Returns the top_k most relevant chunks.
    """
    if not evidence_chunks:
        return []

    q_tokens = tokenize(query)
    if not q_tokens:
        return evidence_chunks[:top_k]

    scored = []
    for chunk in evidence_chunks:
        c_text = chunk.get("text", "")
        c_tokens = tokenize(c_text)
        score = score_text_bm25(q_tokens, c_tokens)
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for score, chunk in scored[:top_k]]

def build_retrieval_context(chunks: List[Dict[str, Any]]) -> str:
    """Format retrieved chunks into verifiable numbered context with citations."""
    if not chunks:
        return "No specific evidence chunks available in database."

    formatted = []
    for i, c in enumerate(chunks, start=1):
        doc_id = c.get("document_id", "DOC")
        page = c.get("page_number", 1)
        sec = c.get("section", "General")
        text = c.get("text", "").strip()
        formatted.append(f"[Evidence #{i} | Doc: {doc_id} | Page: {page} | Section: {sec}]\n{text}")

    return "\n\n---\n\n".join(formatted)
