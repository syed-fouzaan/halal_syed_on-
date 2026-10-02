from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from src.utils.hashing import hash_text

def chunk_document_text(
    doc_id: str,
    text: str,
    source_url: Optional[str] = None,
    pub_date: Optional[date] = None,
    chunk_size: int = 500,
    overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Split document text into structured evidence chunks as required by PRD Section 16:
    - document_id
    - page_number
    - section
    - text
    - content_hash
    - source_url
    - publication_date
    """
    chunks = []
    lines = text.split("\n")
    current_page = 1
    current_section = "General"
    buffer: List[str] = []
    char_count = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--- PAGE") and "---" in stripped:
            try:
                page_part = stripped.split("PAGE")[1].split("---")[0].strip()
                current_page = int(page_part)
            except Exception:
                pass
            continue
        elif stripped.startswith("## ") or stripped.startswith("### "):
            current_section = stripped.lstrip("#").strip()

        buffer.append(line)
        char_count += len(line)

        if char_count >= chunk_size:
            chunk_content = "\n".join(buffer).strip()
            if chunk_content:
                chunks.append({
                    "chunk_id": f"{doc_id}_p{current_page}_{len(chunks)+1}",
                    "document_id": doc_id,
                    "page_number": current_page,
                    "section": current_section,
                    "text": chunk_content,
                    "content_hash": hash_text(chunk_content),
                    "source_url": source_url or "",
                    "publication_date": pub_date.isoformat() if pub_date else ""
                })
            # retain overlap
            buffer = buffer[-3:]
            char_count = sum(len(x) for x in buffer)

    if buffer:
        chunk_content = "\n".join(buffer).strip()
        if chunk_content:
            chunks.append({
                "chunk_id": f"{doc_id}_p{current_page}_{len(chunks)+1}",
                "document_id": doc_id,
                "page_number": current_page,
                "section": current_section,
                "text": chunk_content,
                "content_hash": hash_text(chunk_content),
                "source_url": source_url or "",
                "publication_date": pub_date.isoformat() if pub_date else ""
            })

    return chunks

def save_evidence_chunks(chunks: List[Dict[str, Any]], output_path: str | Path) -> None:
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(chunks, indent=2), encoding="utf-8")

def load_evidence_chunks(input_path: str | Path) -> List[Dict[str, Any]]:
    p = Path(input_path)
    if not p.is_file():
        return []
    return json.loads(p.read_text(encoding="utf-8"))
