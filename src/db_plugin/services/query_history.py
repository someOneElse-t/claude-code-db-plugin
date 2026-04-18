from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path

from db_plugin.models.history import QueryHistoryEntry


DEFAULT_HISTORY_DB = Path.home() / ".claude-code-db-plugin" / "history.db"


class QueryHistoryService:
    """Stores and retrieves query execution history using a local SQLite database."""

    def __init__(self, db_path: str | None = None):
        self._db_path = Path(db_path) if db_path else DEFAULT_HISTORY_DB
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sql TEXT NOT NULL,
                    connection_name TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_time_ms REAL,
                    is_favorite INTEGER DEFAULT 0
                )
                """
            )

    def add(self, sql: str, connection_name: str, status: str, execution_time_ms: float) -> int:
        with sqlite3.connect(str(self._db_path)) as conn:
            cursor = conn.execute(
                "INSERT INTO query_history (sql, connection_name, timestamp, status, execution_time_ms) VALUES (?, ?, ?, ?, ?)",
                (sql, connection_name, datetime.now().isoformat(), status, execution_time_ms),
            )
            return cursor.lastrowid

    def list(self, limit: int = 50) -> list[QueryHistoryEntry]:
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM query_history ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            QueryHistoryEntry(
                id=r["id"],
                sql=r["sql"],
                connection_name=r["connection_name"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                status=r["status"],
                execution_time_ms=r["execution_time_ms"],
                is_favorite=bool(r["is_favorite"]),
            )
            for r in rows
        ]

    def search(self, keyword: str) -> list[QueryHistoryEntry]:
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM query_history WHERE sql LIKE ? ORDER BY timestamp DESC",
                (f"%{keyword}%",),
            ).fetchall()
        return [
            QueryHistoryEntry(
                id=r["id"],
                sql=r["sql"],
                connection_name=r["connection_name"],
                timestamp=datetime.fromisoformat(r["timestamp"]),
                status=r["status"],
                execution_time_ms=r["execution_time_ms"],
                is_favorite=bool(r["is_favorite"]),
            )
            for r in rows
        ]

    def toggle_favorite(self, entry_id: int) -> None:
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute(
                "UPDATE query_history SET is_favorite = NOT is_favorite WHERE id = ?",
                (entry_id,),
            )

    def delete(self, entry_id: int) -> None:
        with sqlite3.connect(str(self._db_path)) as conn:
            conn.execute("DELETE FROM query_history WHERE id = ?", (entry_id,))
