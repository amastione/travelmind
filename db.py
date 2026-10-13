"""SQLite-хранилище TravelMind: пользователи, поездки, расходы."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path("travelmind.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT,
    destination TEXT,
    start_date TEXT,
    end_date TEXT,
    budget REAL,
    currency TEXT,
    people INTEGER,
    data TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    day INTEGER,
    activity_idx INTEGER,
    category TEXT,
    title TEXT,
    cost_plan REAL,
    cost_actual REAL,
    FOREIGN KEY(trip_id) REFERENCES trips(id)
);
"""


@contextmanager
def _conn():
    """Открывает соединение с БД, сохраняет изменения и закрывает его."""
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with _conn() as c:
        c.executescript(SCHEMA)


# ---------- Пользователи ----------

def create_user(username: str, pw_hash: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            (username, pw_hash),
        )


def get_user(username: str):
    with _conn() as c:
        return c.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


# ---------- Поездки ----------

def save_trip(user_id: int, meta: dict, data_json: str) -> int:
    with _conn() as c:
        cur = c.execute(
            """INSERT INTO trips(user_id, title, destination, start_date,
               end_date, budget, currency, people, data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, meta["title"], meta["destination"], meta["start_date"],
             meta["end_date"], meta["budget"], meta["currency"],
             meta["people"], data_json),
        )
        return cur.lastrowid


def list_trips(user_id: int):
    with _conn() as c:
        return c.execute(
            "SELECT * FROM trips WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()


def get_trip(trip_id: int, user_id: int):
    with _conn() as c:
        return c.execute(
            "SELECT * FROM trips WHERE id = ? AND user_id = ?",
            (trip_id, user_id),
        ).fetchone()


def delete_trip(trip_id: int, user_id: int):
    with _conn() as c:
        c.execute("DELETE FROM expenses WHERE trip_id = ?", (trip_id,))
        c.execute(
            "DELETE FROM trips WHERE id = ? AND user_id = ?",
            (trip_id, user_id),
        )


# ---------- Расходы (план / факт) ----------

def init_expenses_from_plan(trip_id: int, data: dict):
    """Создаёт строки расходов из плана, если их ещё нет."""
    with _conn() as c:
        existing = c.execute(
            "SELECT COUNT(*) FROM expenses WHERE trip_id = ?", (trip_id,)
        ).fetchone()[0]
        if existing:
            return
        for d in data.get("days", []):
            for i, a in enumerate(d.get("activities", [])):
                c.execute(
                    """INSERT INTO expenses(trip_id, day, activity_idx,
                       category, title, cost_plan, cost_actual)
                       VALUES (?, ?, ?, ?, ?, ?, NULL)""",
                    (trip_id, d.get("day"), i, a.get("type"),
                     a.get("title"), float(a.get("cost") or 0)),
                )


def get_expenses(trip_id: int):
    with _conn() as c:
        return c.execute(
            """SELECT * FROM expenses WHERE trip_id = ?
               ORDER BY day, activity_idx""",
            (trip_id,),
        ).fetchall()


def update_expense_actual(expense_id: int, actual: float):
    with _conn() as c:
        c.execute(
            "UPDATE expenses SET cost_actual = ? WHERE id = ?",
            (actual, expense_id),
        )


# База создаётся автоматически при импорте этого файла
init()
