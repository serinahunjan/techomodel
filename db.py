import sqlite3
from pathlib import Path
import uuid
from datetime import datetime
import hashlib
import hmac
import os

DB_PATH = Path(__file__).resolve().parent / ("technomodel.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_connection() as conn:

        # =========================
        # ASSESSMENTS TABLE
        # =========================
        conn.execute("""
        CREATE TABLE IF NOT EXISTS assessments (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            total_score INTEGER NOT NULL,
            category TEXT NOT NULL
        );
        """)

        # =========================
        # BREAKDOWN TABLE
        # =========================
        conn.execute("""
        CREATE TABLE IF NOT EXISTS scores_breakdown (
            assessment_id TEXT PRIMARY KEY,
            overload_score INTEGER NOT NULL,
            invasion_score INTEGER NOT NULL,
            complexity_score INTEGER NOT NULL,
            FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
        );
        """)

        # =========================
        # ANSWERS TABLE
        # =========================
        conn.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assessment_id TEXT NOT NULL,
            question_code TEXT NOT NULL,
            answer_value INTEGER NOT NULL,
            FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE
        );
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_answers_assessment_id ON answers(assessment_id);")

        # =========================
        # NEW: SCREEN TIME JOURNAL
        # =========================
        conn.execute("""
        CREATE TABLE IF NOT EXISTS screen_time_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            log_date TEXT NOT NULL,
            hours_used REAL NOT NULL,
            note TEXT,
            UNIQUE(user_email, log_date)
        );
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_salt TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)



# =========================
# EXISTING FUNCTIONS
# =========================
def get_all_assessments():
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, total_score, category
            FROM assessments
            ORDER BY created_at DESC
            """
        ).fetchall()

        return [dict(row) for row in rows]

def save_assessment(total_score: int, category: str) -> str:
    assessment_id = str(uuid.uuid4())
    created_at = datetime.utcnow().isoformat()

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO assessments (id, created_at, total_score, category)
            VALUES (?, ?, ?, ?)
            """,
            (assessment_id, created_at, total_score, category),
        )

    return assessment_id


def get_latest_assessment():
    with get_connection() as conn:

        assessment = conn.execute(
            """
            SELECT id, created_at, total_score, category
            FROM assessments
            ORDER BY created_at DESC
            LIMIT 1
            """
        ).fetchone()

        if not assessment:
            return None

        assessment_id = assessment["id"]

        breakdown = conn.execute(
            """
            SELECT overload_score, invasion_score, complexity_score
            FROM scores_breakdown
            WHERE assessment_id = ?
            """,
            (assessment_id,)
        ).fetchone()

        answers = conn.execute(
            """
            SELECT question_code, answer_value
            FROM answers
            WHERE assessment_id = ?
            ORDER BY question_code
            """,
            (assessment_id,)
        ).fetchall()

        return {
            "assessment": dict(assessment),
            "breakdown": dict(breakdown) if breakdown else None,
            "answers": [
                {
                    "question_code": row["question_code"],
                    "answer_value": row["answer_value"]
                }
                for row in answers
            ]
        }


def save_breakdown(assessment_id: str, overload: int, invasion: int, complexity: int) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO scores_breakdown
                (assessment_id, overload_score, invasion_score, complexity_score)
            VALUES (?, ?, ?, ?)
            """,
            (assessment_id, overload, invasion, complexity),
        )


def save_answers(assessment_id: str, answers: list[int]) -> None:
    with get_connection() as conn:
        rows = []
        for i, value in enumerate(answers):
            rows.append((assessment_id, f"Q{i+1}", int(value)))

        conn.executemany(
            """
            INSERT INTO answers (assessment_id, question_code, answer_value)
            VALUES (?, ?, ?)
            """,
            rows
        )


# =========================
# (JOURNAL)
# =========================

def save_screen_time_log(user_email: str, log_date: str, hours_used: float, note: str = "") -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO screen_time_logs (user_email, log_date, hours_used, note)
            VALUES (?, ?, ?, ?)
            """,
            (user_email, log_date, hours_used, note),
        )


def get_user_screen_time_logs(user_email: str):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT log_date, hours_used, note
            FROM screen_time_logs
            WHERE user_email = ?
            ORDER BY log_date DESC
            """,
            (user_email,)
        ).fetchall()

        return [
            {
                "log_date": row["log_date"],
                "hours_used": row["hours_used"],
                "note": row["note"]
            }
            for row in rows
        ]
def delete_screen_time_log(user_email: str, log_date: str) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            """
            DELETE FROM screen_time_logs
            WHERE user_email = ? AND log_date = ?
            """,
            (user_email, log_date),
        )
        return cursor.rowcount > 0

if __name__ == "__main__":
    init_db()
    print("Database created / updated successfully.")

def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    ).hex()

    return salt.hex(), password_hash


def create_user(first_name, last_name, email, password):
    salt, password_hash = hash_password(password)

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO users (id, first_name, last_name, email, password_salt, password_hash, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            str(uuid.uuid4()),
            first_name,
            last_name,
            email.lower(),
            salt,
            password_hash,
            datetime.utcnow().isoformat()
        ))


def verify_user(email, password):
    with get_connection() as conn:
        user = conn.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email.lower(),)).fetchone()

        if not user:
            return None

        _, password_hash = hash_password(password, bytes.fromhex(user["password_salt"]))

        if not hmac.compare_digest(password_hash, user["password_hash"]):
            return None

        return {
            "id": user["id"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "email": user["email"]
        }
