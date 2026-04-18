from dataclasses import dataclass
from datetime import datetime


@dataclass
class QueryHistoryEntry:
    id: int
    sql: str
    connection_name: str
    timestamp: datetime
    status: str  # "success" | "error"
    execution_time_ms: float
    is_favorite: bool = False
