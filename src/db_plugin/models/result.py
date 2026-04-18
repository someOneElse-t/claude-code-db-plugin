from dataclasses import dataclass


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[dict]
    row_count: int
    execution_time_ms: float
    error_message: str | None = None
