from typing import Any, Dict, List, Optional
import pandas as pd

def detect_document_hash_changes(previous_hash: Optional[str], current_hash: str) -> bool:
    """Detect whether official document content has changed."""
    if not previous_hash:
        return False
    return previous_hash != current_hash

def compare_portfolio_snapshots(old_df: pd.DataFrame, new_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare two portfolio snapshots to detect added holdings, removed holdings,
    and significant weight shifts (> 1.0%).
    """
    if old_df.empty or new_df.empty:
        return {"has_changes": False, "added": [], "removed": [], "weight_changes": []}

    old_map = dict(zip(old_df["company_name"], old_df["weight_pct"]))
    new_map = dict(zip(new_df["company_name"], new_df["weight_pct"]))

    added = [{"company_name": c, "weight_pct": new_map[c]} for c in new_map if c not in old_map]
    removed = [{"company_name": c, "weight_pct": old_map[c]} for c in old_map if c not in new_map]
    
    weight_changes = []
    for c in new_map:
        if c in old_map:
            diff = round(float(new_map[c]) - float(old_map[c]), 3)
            if abs(diff) >= 0.5:
                weight_changes.append({
                    "company_name": c,
                    "old_weight": old_map[c],
                    "new_weight": new_map[c],
                    "change": diff
                })

    has_changes = bool(added or removed or weight_changes)
    return {
        "has_changes": has_changes,
        "added": added,
        "removed": removed,
        "weight_changes": weight_changes
    }
