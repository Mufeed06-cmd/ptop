from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional
from schemas import Question, Profile


DB_PATH = Path(__file__).parent / "learnmate.db"


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Returns a SQLite connection with row_factory enabled."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path = DB_PATH) -> None:
    """
    Initializes SQLite tables:
    - sessions
    - questions
    - attempts
    - mastery(concept_id, score default 0.5)
    """
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                topic TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS questions (
                id TEXT PRIMARY KEY,
                concept_id TEXT NOT NULL,
                question TEXT NOT NULL,
                options TEXT NOT NULL,
                correct_index INTEGER NOT NULL,
                explanation TEXT,
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            );

            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question_id TEXT NOT NULL,
                selected_index INTEGER NOT NULL,
                outcome REAL NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id),
                FOREIGN KEY (question_id) REFERENCES questions(id)
            );

            CREATE TABLE IF NOT EXISTS mastery (
                concept_id TEXT PRIMARY KEY,
                score REAL DEFAULT 0.5
            );
            """
        )
        conn.commit()


# Initialize tables upon module load
init_db()


def save_session(session_id: str, user_id: str, topic: str = "Python Loops") -> None:
    """Inserts or replaces a session entry."""
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (id, user_id, topic) VALUES (?, ?, ?)",
            (session_id, user_id, topic),
        )
        conn.commit()


def save_question(q: Question, session_id: Optional[str] = None) -> None:
    """Saves or updates a question in the SQLite database."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO questions 
            (id, concept_id, question, options, correct_index, explanation, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                q.id,
                q.concept_id,
                q.question,
                json.dumps(q.options),
                q.correct_index,
                q.explanation,
                session_id,
            ),
        )
        conn.commit()


def save_questions(questions: list[Question], session_id: Optional[str] = None) -> None:
    """Batch saves questions."""
    for q in questions:
        save_question(q, session_id=session_id)


def get_question(question_id: str) -> Optional[Question]:
    """Retrieves a question by its id from SQLite."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return Question(
            id=row["id"],
            concept_id=row["concept_id"],
            question=row["question"],
            options=json.loads(row["options"]),
            correct_index=row["correct_index"],
            explanation=row["explanation"] or "",
        )


def record_attempt(
    session_id: Optional[str],
    question_id: str,
    selected_index: int,
    outcome: float,
) -> None:
    """Inserts an attempt record into the attempts table."""
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO attempts (session_id, question_id, selected_index, outcome)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, question_id, selected_index, outcome),
        )
        conn.commit()


def get_mastery(concept_id: str) -> float:
    """
    Retrieves the current mastery score for a concept.
    Defaults to 0.5 if not previously recorded.
    """
    with get_connection() as conn:
        cursor = conn.execute("SELECT score FROM mastery WHERE concept_id = ?", (concept_id,))
        row = cursor.fetchone()
        if row is not None:
            return float(row["score"])
        # If not present, initialize with default 0.5
        conn.execute("INSERT OR IGNORE INTO mastery (concept_id, score) VALUES (?, 0.5)", (concept_id,))
        conn.commit()
        return 0.5


def update_mastery(concept_id: str, new_score: float) -> None:
    """Sets or updates the mastery score for a concept."""
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO mastery (concept_id, score) VALUES (?, ?) ON CONFLICT(concept_id) DO UPDATE SET score = excluded.score",
            (concept_id, new_score),
        )
        conn.commit()


def get_all_mastery() -> dict[str, float]:
    """Returns all concept mastery scores."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT concept_id, score FROM mastery")
        return {row["concept_id"]: float(row["score"]) for row in cursor.fetchall()}


def reset_db() -> None:
    """Clears all table contents (useful for testing)."""
    with get_connection() as conn:
        conn.executescript(
            """
            DELETE FROM attempts;
            DELETE FROM questions;
            DELETE FROM sessions;
            DELETE FROM mastery;
            """
        )
        conn.commit()
