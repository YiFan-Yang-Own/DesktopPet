"""Vocabulary loading, scheduling, and learning-record persistence."""

from __future__ import annotations

import csv
import json
import logging
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from core.config_manager import ConfigManager


LOGGER = logging.getLogger(__name__)
REVIEW_INTERVALS = [1, 3, 7, 30]


class WordManager:
    """Manage word libraries and simplified spaced repetition records."""

    def __init__(
        self,
        config_manager: ConfigManager,
        database_path: Path,
        wordlib_dir: Path,
    ) -> None:
        """Initialize SQLite storage and load the configured word library."""
        self.config_manager = config_manager
        self.database_path = database_path
        self.wordlib_dir = wordlib_dir
        self.recent_word_ids: List[int] = []
        self.deferred_word_ids: List[int] = []

        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.database_path))
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
        self.refresh_word_library()

    def _create_tables(self) -> None:
        """Create database tables if they do not already exist."""
        with self.connection:
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word TEXT NOT NULL UNIQUE,
                    phonetic TEXT,
                    meaning TEXT NOT NULL,
                    example TEXT,
                    level TEXT,
                    last_shown_at TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._ensure_column("vocabulary", "last_shown_at", "TEXT")
            self.connection.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_record (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    word_id INTEGER NOT NULL,
                    reviewed_at TEXT NOT NULL,
                    result TEXT NOT NULL CHECK(result IN ('remembered', 'again')),
                    FOREIGN KEY(word_id) REFERENCES vocabulary(id)
                )
                """
            )

    def refresh_word_library(self) -> None:
        """Load the selected JSON word library into the vocabulary table."""
        word_lib = str(self.config_manager.get("word_lib", "cet4.json"))
        word_file = self.wordlib_dir / word_lib
        if not word_file.exists():
            LOGGER.warning("Configured word library %s not found; using cet4.json", word_file)
            word_file = self.wordlib_dir / "cet4.json"

        level = word_file.stem.upper()
        try:
            with word_file.open("r", encoding="utf-8") as file:
                words = json.load(file)
        except (OSError, json.JSONDecodeError):
            LOGGER.exception("Failed to load word library %s", word_file)
            words = []

        with self.connection:
            for item in words:
                self.connection.execute(
                    """
                    INSERT OR IGNORE INTO vocabulary
                    (word, phonetic, meaning, example, level, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item.get("word", ""),
                        item.get("phonetic", ""),
                        item.get("meaning", ""),
                        item.get("example", ""),
                        level,
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
        LOGGER.info("Word library refreshed from %s", word_file)

    def get_next_word(self) -> Optional[Dict[str, object]]:
        """Return the next new or due review word using simplified intervals."""
        if self.deferred_word_ids:
            word_id = self.deferred_word_ids.pop(0)
            word = self._get_word_by_id(word_id)
            if word is not None:
                self._mark_recent(word_id)
                self._mark_shown(word_id)
                return word

        word = self._get_new_word()
        if word is not None:
            word_id = int(word["id"])
            self._mark_recent(word_id)
            self._mark_shown(word_id)
            return word

        word = self._get_due_review_word()
        if word is not None:
            word_id = int(word["id"])
            self._mark_recent(word_id)
            self._mark_shown(word_id)
            return word

        LOGGER.info("No word is currently due for reminder")
        return None

    def record_result(self, word_id: int, result: str) -> None:
        """Record a user's response to a reminder bubble."""
        if result not in {"remembered", "again"}:
            raise ValueError(f"Unsupported learning result: {result}")

        with self.connection:
            self.connection.execute(
                """
                INSERT INTO learning_record (word_id, reviewed_at, result)
                VALUES (?, ?, ?)
                """,
                (word_id, datetime.now().isoformat(timespec="seconds"), result),
            )
        LOGGER.info("Recorded learning result for word_id=%s result=%s", word_id, result)

        if result == "again":
            self.defer_word(word_id, high_priority=True)

    def defer_word(self, word_id: int, high_priority: bool = False) -> None:
        """Put a word back into the pending queue for a future reminder."""
        if word_id in self.deferred_word_ids:
            return
        if high_priority:
            self.deferred_word_ids.insert(0, word_id)
        else:
            self.deferred_word_ids.append(word_id)

    def get_today_stats(self) -> Dict[str, int]:
        """Return today's learning summary."""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        rows = self.connection.execute(
            """
            SELECT lr.word_id, lr.reviewed_at, lr.result,
                   (SELECT COUNT(*) FROM learning_record prev
                    WHERE prev.word_id = lr.word_id
                      AND prev.reviewed_at < lr.reviewed_at) AS previous_count
            FROM learning_record lr
            WHERE lr.reviewed_at >= ?
            """,
            (today_start.isoformat(timespec="seconds"),),
        ).fetchall()

        new_words = sum(1 for row in rows if int(row["previous_count"]) == 0)
        reviews = len(rows) - new_words
        remembered = sum(1 for row in rows if row["result"] == "remembered")
        again = len(rows) - remembered
        return {
            "new_words": new_words,
            "reviews": reviews,
            "remembered": remembered,
            "again": again,
            "total": len(rows),
        }

    def get_overall_stats(self) -> Dict[str, int]:
        """Return cumulative learning statistics."""
        total_words = self.connection.execute(
            "SELECT COUNT(*) AS count FROM vocabulary"
        ).fetchone()["count"]
        learned_words = self.connection.execute(
            "SELECT COUNT(DISTINCT word_id) AS count FROM learning_record"
        ).fetchone()["count"]
        total_records = self.connection.execute(
            "SELECT COUNT(*) AS count FROM learning_record"
        ).fetchone()["count"]
        remembered = self.connection.execute(
            "SELECT COUNT(*) AS count FROM learning_record WHERE result = 'remembered'"
        ).fetchone()["count"]
        again = self.connection.execute(
            "SELECT COUNT(*) AS count FROM learning_record WHERE result = 'again'"
        ).fetchone()["count"]
        return {
            "total_words": int(total_words),
            "learned_words": int(learned_words),
            "remaining_words": max(int(total_words) - int(learned_words), 0),
            "total_records": int(total_records),
            "remembered": int(remembered),
            "again": int(again),
        }

    def get_weak_word_count(self, query: str = "") -> int:
        """Return the number of words that have been answered again at least once."""
        search_clause, params = self._build_search_clause(
            query,
            [
                "v.word",
                "v.phonetic",
                "v.meaning",
                "v.example",
                "v.level",
                "lr.reviewed_at",
                "lr.result",
            ],
        )
        row = self.connection.execute(
            f"""
            SELECT COUNT(*) AS count
            FROM (
                SELECT v.id
                FROM vocabulary v
                JOIN learning_record lr ON lr.word_id = v.id
                WHERE 1 = 1
                  {search_clause}
                GROUP BY v.id
                HAVING SUM(CASE WHEN lr.result = 'again' THEN 1 ELSE 0 END) > 0
            )
            """,
            params,
        ).fetchone()
        return int(row["count"])

    def get_weak_words(self, limit: int = 20, query: str = "") -> List[Dict[str, object]]:
        """Return weak words ranked by how often they were missed."""
        search_clause, params = self._build_search_clause(
            query,
            [
                "v.word",
                "v.phonetic",
                "v.meaning",
                "v.example",
                "v.level",
                "lr.reviewed_at",
                "lr.result",
            ],
        )
        rows = self.connection.execute(
            f"""
            SELECT v.id, v.word, v.phonetic, v.meaning, v.example, v.level,
                   MAX(lr.reviewed_at) AS last_reviewed_at,
                   SUM(CASE WHEN lr.result = 'remembered' THEN 1 ELSE 0 END) AS remembered_count,
                   SUM(CASE WHEN lr.result = 'again' THEN 1 ELSE 0 END) AS again_count,
                   MAX(CASE WHEN lr.result = 'again' THEN lr.reviewed_at ELSE NULL END) AS last_again_at
            FROM vocabulary v
            JOIN learning_record lr ON lr.word_id = v.id
            WHERE 1 = 1
              {search_clause}
            GROUP BY v.id
            HAVING SUM(CASE WHEN lr.result = 'again' THEN 1 ELSE 0 END) > 0
            ORDER BY again_count DESC, last_reviewed_at DESC, v.id ASC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def get_recent_records(self, limit: int = 20, query: str = "") -> List[Dict[str, object]]:
        """Return recent learning records with word details."""
        search_clause, params = self._build_search_clause(
            query,
            [
                "lr.reviewed_at",
                "lr.result",
                "v.word",
                "v.phonetic",
                "v.meaning",
                "v.example",
                "v.level",
            ],
        )
        rows = self.connection.execute(
            f"""
            SELECT lr.id, lr.word_id, lr.reviewed_at, lr.result,
                   v.word, v.phonetic, v.meaning, v.example, v.level
            FROM learning_record lr
            JOIN vocabulary v ON v.id = lr.word_id
            WHERE 1 = 1
              {search_clause}
            ORDER BY lr.reviewed_at DESC, lr.id DESC
            LIMIT ?
            """,
            (*params, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def export_records_csv(self, export_path: Path) -> int:
        """Export all learning records to a CSV file and return the row count."""
        rows = self.connection.execute(
            """
            SELECT lr.reviewed_at, lr.result,
                   v.word, v.phonetic, v.meaning, v.example, v.level
            FROM learning_record lr
            JOIN vocabulary v ON v.id = lr.word_id
            ORDER BY lr.reviewed_at ASC, lr.id ASC
            """
        ).fetchall()
        export_path.parent.mkdir(parents=True, exist_ok=True)
        with export_path.open("w", encoding="utf-8-sig", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["reviewed_at", "result", "word", "phonetic", "meaning", "example", "level"]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["reviewed_at"],
                        row["result"],
                        row["word"],
                        row["phonetic"],
                        row["meaning"],
                        row["example"],
                        row["level"],
                    ]
                )
        return len(rows)

    def get_weak_review_word(self) -> Optional[Dict[str, object]]:
        """Return the most frequently missed word that has not been shown recently."""
        recent_filter = ""
        params: List[int] = []
        if self.recent_word_ids:
            placeholders = ",".join("?" for _ in self.recent_word_ids)
            recent_filter = f"AND v.id NOT IN ({placeholders})"
            params = self.recent_word_ids

        query = f"""
            SELECT v.id, v.word, v.phonetic, v.meaning, v.example, v.level,
                   MAX(lr.reviewed_at) AS last_reviewed_at,
                   SUM(CASE WHEN lr.result = 'remembered' THEN 1 ELSE 0 END) AS remembered_count,
                   SUM(CASE WHEN lr.result = 'again' THEN 1 ELSE 0 END) AS again_count,
                   MAX(CASE WHEN lr.result = 'again' THEN lr.reviewed_at ELSE NULL END) AS last_again_at
            FROM vocabulary v
            JOIN learning_record lr ON lr.word_id = v.id
            WHERE 1 = 1
              {recent_filter}
            GROUP BY v.id
            HAVING SUM(CASE WHEN lr.result = 'again' THEN 1 ELSE 0 END) > 0
            ORDER BY again_count DESC, last_reviewed_at ASC, v.id ASC
            LIMIT 1
        """
        row = self.connection.execute(query, params).fetchone()
        return self._row_to_word(row)

    def reset_learning_records(self) -> None:
        """Delete local learning progress while keeping imported vocabulary."""
        with self.connection:
            self.connection.execute("DELETE FROM learning_record")
            self.connection.execute("UPDATE vocabulary SET last_shown_at = NULL")
        self.recent_word_ids.clear()
        self.deferred_word_ids.clear()

    def get_due_count(self) -> int:
        """Return the number of words that are due for review now."""
        rows = self.connection.execute(
            """
            SELECT v.id,
                   MAX(lr.reviewed_at) AS last_reviewed_at,
                   SUM(CASE WHEN lr.result = 'remembered' THEN 1 ELSE 0 END) AS remembered_count,
                   MAX(CASE WHEN lr.result = 'again' THEN lr.reviewed_at ELSE NULL END) AS last_again_at
            FROM vocabulary v
            JOIN learning_record lr ON lr.word_id = v.id
            GROUP BY v.id
            """
        ).fetchall()
        now = datetime.now()
        return sum(1 for row in rows if self._is_due(row, now))

    def get_streak_days(self) -> int:
        """Return consecutive learning days ending today."""
        rows = self.connection.execute(
            """
            SELECT DISTINCT substr(reviewed_at, 1, 10) AS reviewed_date
            FROM learning_record
            ORDER BY reviewed_date DESC
            """
        ).fetchall()
        learned_dates = {date.fromisoformat(row["reviewed_date"]) for row in rows}
        streak = 0
        cursor = date.today()
        while cursor in learned_dates:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    def close(self) -> None:
        """Close the SQLite connection."""
        self.connection.close()

    def _ensure_column(self, table_name: str, column_name: str, definition: str) -> None:
        """Add a missing column to an existing SQLite table."""
        columns = self.connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        if column_name in {row["name"] for row in columns}:
            return
        self.connection.execute(
            f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"
        )

    @staticmethod
    def _build_search_clause(query: str, columns: List[str]) -> tuple[str, List[str]]:
        """Build a case-insensitive LIKE clause for multiple text columns."""
        term = query.strip().lower()
        if not term:
            return "", []

        pattern = f"%{term}%"
        clause = " AND (" + " OR ".join(
            f"LOWER(COALESCE({column}, '')) LIKE ?" for column in columns
        ) + ")"
        return clause, [pattern] * len(columns)

    def _get_new_word(self) -> Optional[Dict[str, object]]:
        """Return an unstudied word, excluding very recent reminders."""
        recent_filter = ""
        params: List[int] = []
        if self.recent_word_ids:
            placeholders = ",".join("?" for _ in self.recent_word_ids)
            recent_filter = f"AND id NOT IN ({placeholders})"
            params = self.recent_word_ids

        query = f"""
            SELECT *
            FROM vocabulary
            WHERE id NOT IN (SELECT DISTINCT word_id FROM learning_record)
              {recent_filter}
            ORDER BY
              CASE WHEN last_shown_at IS NULL THEN 0 ELSE 1 END,
              COALESCE(last_shown_at, created_at) ASC,
              id ASC
            LIMIT 1
        """
        row = self.connection.execute(query, params).fetchone()
        return self._row_to_word(row)

    def _get_due_review_word(self) -> Optional[Dict[str, object]]:
        """Return the review word with the oldest due time."""
        rows = self.connection.execute(
            """
            SELECT v.*,
                   MAX(lr.reviewed_at) AS last_reviewed_at,
                   SUM(CASE WHEN lr.result = 'remembered' THEN 1 ELSE 0 END) AS remembered_count,
                   MAX(CASE WHEN lr.result = 'again' THEN lr.reviewed_at ELSE NULL END) AS last_again_at
            FROM vocabulary v
            JOIN learning_record lr ON lr.word_id = v.id
            GROUP BY v.id
            ORDER BY last_reviewed_at ASC
            """
        ).fetchall()

        now = datetime.now()
        for row in rows:
            word_id = int(row["id"])
            if word_id in self.recent_word_ids:
                continue
            if self._is_due(row, now):
                return self._row_to_word(row)
        return None

    def _is_due(self, row: sqlite3.Row, now: datetime) -> bool:
        """Determine whether a reviewed word is due again."""
        last_reviewed = datetime.fromisoformat(row["last_reviewed_at"])
        last_again = row["last_again_at"]
        if last_again and last_again == row["last_reviewed_at"]:
            return True

        remembered_count = int(row["remembered_count"] or 0)
        interval_index = min(max(remembered_count - 1, 0), len(REVIEW_INTERVALS) - 1)
        due_at = last_reviewed + timedelta(days=REVIEW_INTERVALS[interval_index])
        return now >= due_at

    def _get_word_by_id(self, word_id: int) -> Optional[Dict[str, object]]:
        """Return a word by primary key."""
        row = self.connection.execute(
            "SELECT * FROM vocabulary WHERE id = ?",
            (word_id,),
        ).fetchone()
        return self._row_to_word(row)

    @staticmethod
    def _row_to_word(row: Optional[sqlite3.Row]) -> Optional[Dict[str, object]]:
        """Convert a SQLite row into a plain word dictionary."""
        if row is None:
            return None
        return {
            "id": row["id"],
            "word": row["word"],
            "phonetic": row["phonetic"],
            "meaning": row["meaning"],
            "example": row["example"],
            "level": row["level"],
        }

    def _mark_recent(self, word_id: int) -> None:
        """Remember recently pushed words to avoid immediate repetition."""
        self.recent_word_ids.append(word_id)
        self.recent_word_ids = self.recent_word_ids[-5:]

    def _mark_shown(self, word_id: int) -> None:
        """Persist the last time a word was shown."""
        with self.connection:
            self.connection.execute(
                "UPDATE vocabulary SET last_shown_at = ? WHERE id = ?",
                (datetime.now().isoformat(timespec="seconds"), word_id),
            )
