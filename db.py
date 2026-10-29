"""SQLite-хранилище TravelMind: пользователи, сессии, поездки, расходы."""
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

CREATE TABLE IF NOT EXISTS auth_sessions (
    token_hash TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires_at INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_user_id
ON auth_sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_auth_sessions_expires_at
ON auth_sessions(expires_at);

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
    """Открывает соединение с базой, сохраняет изменения и закрывает его."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init():
    """Создаёт таблицы и индексы, если их ещё нет."""
    with _conn() as connection:
        connection.executescript(SCHEMA)


# ==========================================================
# ПОЛЬЗОВАТЕЛИ
# ==========================================================

def create_user(username: str, pw_hash: str):
    """Создаёт пользователя."""
    with _conn() as connection:
        connection.execute(
            "INSERT INTO users(username, password_hash) VALUES (?, ?)",
            (username, pw_hash),
        )


def get_user(username: str):
    """Находит пользователя по логину."""
    with _conn() as connection:
        return connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()


# ==========================================================
# ПОСТОЯННЫЕ СЕССИИ
# ==========================================================

def create_auth_session(
    user_id: int,
    token_hash: str,
    expires_at: int,
):
    """Сохраняет хэш токена авторизации."""
    with _conn() as connection:
        connection.execute(
            """
            INSERT INTO auth_sessions(token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (token_hash, user_id, expires_at),
        )


def get_user_by_session_token(token_hash: str):
    """
    Возвращает пользователя по активному токену.

    Перед проверкой автоматически удаляет устаревшие токены.
    """
    with _conn() as connection:
        connection.execute(
            """
            DELETE FROM auth_sessions
            WHERE expires_at < CAST(strftime('%s', 'now') AS INTEGER)
            """
        )

        return connection.execute(
            """
            SELECT users.*
            FROM auth_sessions
            INNER JOIN users ON users.id = auth_sessions.user_id
            WHERE auth_sessions.token_hash = ?
              AND auth_sessions.expires_at >=
                  CAST(strftime('%s', 'now') AS INTEGER)
            """,
            (token_hash,),
        ).fetchone()


def delete_auth_session(token_hash: str):
    """Удаляет токен из БД при выходе пользователя."""
    with _conn() as connection:
        connection.execute(
            "DELETE FROM auth_sessions WHERE token_hash = ?",
            (token_hash,),
        )


# ==========================================================
# ПОЕЗДКИ
# ==========================================================

def save_trip(user_id: int, meta: dict, data_json: str) -> int:
    """Сохраняет новую поездку и возвращает её ID."""
    with _conn() as connection:
        cursor = connection.execute(
            """
            INSERT INTO trips(
                user_id,
                title,
                destination,
                start_date,
                end_date,
                budget,
                currency,
                people,
                data
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                meta["title"],
                meta["destination"],
                meta["start_date"],
                meta["end_date"],
                meta["budget"],
                meta["currency"],
                meta["people"],
                data_json,
            ),
        )

        return cursor.lastrowid


def list_trips(user_id: int):
    """Возвращает список поездок пользователя."""
    with _conn() as connection:
        return connection.execute(
            """
            SELECT *
            FROM trips
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (user_id,),
        ).fetchall()


def get_trip(trip_id: int, user_id: int):
    """Возвращает одну поездку, если она принадлежит пользователю."""
    with _conn() as connection:
        return connection.execute(
            """
            SELECT *
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()


def delete_trip(trip_id: int, user_id: int):
    """Удаляет поездку и связанные с ней расходы."""
    with _conn() as connection:
        connection.execute(
            "DELETE FROM expenses WHERE trip_id = ?",
            (trip_id,),
        )

        connection.execute(
            """
            DELETE FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        )

# ==========================================================
# AI-РЕДАКТИРОВАНИЕ СОХРАНЁННОГО МАРШРУТА
# ==========================================================

def update_trip_from_ai(
    trip_id: int,
    user_id: int,
    updated_data: dict,
):
    """
    Сохраняет маршрут после AI-редактирования.

    Обновляет:
    - JSON-маршрут trips.data;
    - название trips.title;
    - бюджет trips.budget на основе total_cost.

    Плановые расходы пересоздаются по новому маршруту.
    Фактические расходы сохраняются, если совпали:
    день + категория + название активности.
    """
    import json

    with _conn() as connection:
        trip = connection.execute(
            """
            SELECT *
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()

        if not trip:
            raise ValueError("Поездка не найдена или недоступна.")

        # Сохраняем введённые пользователем фактические расходы,
        # чтобы они не исчезли после изменения маршрута AI.
        old_expenses = connection.execute(
            """
            SELECT day, category, title, cost_actual
            FROM expenses
            WHERE trip_id = ?
            """,
            (trip_id,),
        ).fetchall()

        actual_costs = {}

        for expense in old_expenses:
            key = (
                expense["day"],
                expense["category"],
                expense["title"],
            )

            actual_costs[key] = expense["cost_actual"]

        # Удаляем старый план расходов.
        connection.execute(
            "DELETE FROM expenses WHERE trip_id = ?",
            (trip_id,),
        )

        # Сохраняем новый JSON и базовые данные поездки.
        connection.execute(
            """
            UPDATE trips
            SET
                title = ?,
                budget = ?,
                data = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                updated_data.get("title") or trip["title"],
                float(updated_data.get("total_cost") or trip["budget"] or 0),
                json.dumps(updated_data, ensure_ascii=False),
                trip_id,
                user_id,
            ),
        )

        # Создаём обновлённые плановые расходы.
        for day_data in updated_data.get("days", []):
            for index, activity in enumerate(
                day_data.get("activities", [])
            ):
                day_number = day_data.get("day")
                category = activity.get("type")
                title = activity.get("title")

                expense_key = (
                    day_number,
                    category,
                    title,
                )

                saved_actual = actual_costs.get(expense_key)

                connection.execute(
                    """
                    INSERT INTO expenses(
                        trip_id,
                        day,
                        activity_idx,
                        category,
                        title,
                        cost_plan,
                        cost_actual
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        trip_id,
                        day_number,
                        index,
                        category,
                        title,
                        float(activity.get("cost") or 0),
                        saved_actual,
                    ),
                )
# ==========================================================
# РАСХОДЫ: ПЛАН / ФАКТ
# ==========================================================

def init_expenses_from_plan(trip_id: int, data: dict):
    """Создаёт строки расходов на основе маршрута AI, если их ещё нет."""
    with _conn() as connection:
        existing = connection.execute(
            "SELECT COUNT(*) FROM expenses WHERE trip_id = ?",
            (trip_id,),
        ).fetchone()[0]

        if existing:
            return

        for day_data in data.get("days", []):
            for index, activity in enumerate(
                day_data.get("activities", [])
            ):
                connection.execute(
                    """
                    INSERT INTO expenses(
                        trip_id,
                        day,
                        activity_idx,
                        category,
                        title,
                        cost_plan,
                        cost_actual
                    )
                    VALUES (?, ?, ?, ?, ?, ?, NULL)
                    """,
                    (
                        trip_id,
                        day_data.get("day"),
                        index,
                        activity.get("type"),
                        activity.get("title"),
                        float(activity.get("cost") or 0),
                    ),
                )


def get_expenses(trip_id: int):
    """Возвращает все плановые и фактические расходы поездки."""
    with _conn() as connection:
        return connection.execute(
            """
            SELECT *
            FROM expenses
            WHERE trip_id = ?
            ORDER BY day, activity_idx
            """,
            (trip_id,),
        ).fetchall()


def update_expense_actual(expense_id: int, actual: float):
    """Обновляет фактическую сумму расхода."""
    with _conn() as connection:
        connection.execute(
            """
            UPDATE expenses
            SET cost_actual = ?
            WHERE id = ?
            """,
            (actual, expense_id),
        )


# Создание базы при импорте модуля.
init()
