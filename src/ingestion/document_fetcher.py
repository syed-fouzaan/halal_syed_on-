from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional
import pypdf
from src.utils.hashing import hash_file, hash_text
from src.utils.logging import get_logger

logger = get_logger("document_fetcher")

def extract_text_from_pdf(file_path: str | Path) -> str:
    """Extract full text from a PDF file."""
    p = Path(file_path)
    if not p.is_file():
        return ""
    try:
        reader = pypdf.PdfReader(str(p))
        text_blocks = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            text_blocks.append(f"--- PAGE {i+1} ---\n{page_text}")
        return "\n\n".join(text_blocks)
    except Exception as e:
        logger.error(f"Error reading PDF {p}: {e}")
        return ""

def register_document(
    fund_id: str,
    doc_type: str,
    title: str,
    local_path: str | Path,
    source_url: Optional[str] = None,
    pub_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Register document, verify/compute cryptographic SHA-256 hash, and return document record.
    """
    p = Path(local_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {local_path}")
    
    content_hash = hash_file(p)
    doc_id = f"DOC_{fund_id}_{p.stem}"
    
    return {
        "document_id": doc_id,
        "fund_id": fund_id,
        "document_type": doc_type,
        "title": title,
        "publication_date": pub_date or date.today(),
        "source_url": source_url or f"file://{p.resolve()}",
        "local_path": str(p),
        "content_hash": content_hash,
        "retrieved_at": datetime.now()
    }
