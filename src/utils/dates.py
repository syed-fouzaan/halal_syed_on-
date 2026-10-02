from datetime import date, datetime
from typing import Optional

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d-%b-%Y",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%d-%B-%Y"
]

def parse_date(date_str: str | date | datetime) -> Optional[date]:
    """Parse string or date into datetime.date object."""
    if isinstance(date_str, date) and not isinstance(date_str, datetime):
        return date_str
    if isinstance(date_str, datetime):
        return date_str.date()
    if not date_str or not isinstance(date_str, str):
        return None
    cleaned = date_str.strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None

def format_date_iso(d: date | datetime | None) -> str:
    """Format date as YYYY-MM-DD."""
    if not d:
        return ""
    if isinstance(d, datetime):
        return d.date().isoformat()
    return d.isoformat()
