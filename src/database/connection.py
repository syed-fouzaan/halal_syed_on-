from pathlib import Path
import duckdb

DEFAULT_DB_PATH = Path("data/database/halal_sip.duckdb")

def get_db_connection(db_path: str | Path = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    """Return a DuckDB connection, creating parent directory if necessary."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))
