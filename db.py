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
    is_manual INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY(trip_id) REFERENCES trips(id)
);

CREATE TABLE IF NOT EXISTS trip_checklist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id INTEGER NOT NULL,
    item_key TEXT NOT NULL,
    is_completed INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(trip_id, item_key),
    FOREIGN KEY(trip_id) REFERENCES trips(id)
);

CREATE INDEX IF NOT EXISTS idx_checklist_items_trip_id
ON trip_checklist_items(trip_id);

CREATE TABLE IF NOT EXISTS trip_activity_visits (
    trip_id INTEGER NOT NULL,
    activity_key TEXT NOT NULL,
    is_visited INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (trip_id, activity_key),
    FOREIGN KEY(trip_id) REFERENCES trips(id)
);
"""
"""
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
    """Создаёт таблицы, индексы и обновляет схему при необходимости."""
    with _conn() as connection:
        connection.executescript(SCHEMA)

        expense_columns = connection.execute(
            "PRAGMA table_info(expenses)"
        ).fetchall()

        column_names = {
            column["name"]
            for column in expense_columns
        }

        if "is_manual" not in column_names:
            connection.execute(
                """
                ALTER TABLE expenses
                ADD COLUMN is_manual INTEGER NOT NULL DEFAULT 0
                """
            )

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
    """Удаляет поездку, её расходы и отметки чек-листа."""
    with _conn() as connection:
        # Сначала убеждаемся, что поездка действительно принадлежит пользователю.
        trip = connection.execute(
            """
            SELECT id
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()

        if not trip:
            raise ValueError("Поездка не найдена или недоступна.")

        connection.execute(
            "DELETE FROM expenses WHERE trip_id = ?",
            (trip_id,),
        )

        connection.execute(
            "DELETE FROM trip_checklist_items WHERE trip_id = ?",
            (trip_id,),
        )
        connection.execute(
            "DELETE FROM trip_activity_visits WHERE trip_id = ?",
            (trip_id,),
        )
        connection.execute(
            "DELETE FROM trips WHERE id = ? AND user_id = ?",
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
              AND is_manual = 0
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
            """
            DELETE FROM expenses
            WHERE trip_id = ?
              AND is_manual = 0
            """,
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

def get_manual_expenses(trip_id: int):
    """Возвращает расходы, которые пользователь добавил вручную."""
    with _conn() as connection:
        return connection.execute(
            """
            SELECT *
            FROM expenses
            WHERE trip_id = ?
              AND is_manual = 1
            ORDER BY day DESC, id DESC
            """,
            (trip_id,),
        ).fetchall()
def update_manual_expense(
    expense_id: int,
    trip_id: int,
    user_id: int,
    day: int,
    category: str,
    title: str,
    cost_plan: float,
    cost_actual: float,
):
    """Обновляет ручной расход, если он принадлежит пользователю."""
    clean_title = str(title).strip()

    if not clean_title:
        raise ValueError("Укажите название расхода.")

    with _conn() as connection:
        expense = connection.execute(
            """
            SELECT expenses.id
            FROM expenses
            INNER JOIN trips ON trips.id = expenses.trip_id
            WHERE expenses.id = ?
              AND expenses.trip_id = ?
              AND trips.user_id = ?
              AND expenses.is_manual = 1
            """,
            (expense_id, trip_id, user_id),
        ).fetchone()

        if not expense:
            raise ValueError(
                "Ручной расход не найден или недоступен для изменения."
            )

        connection.execute(
            """
            UPDATE expenses
            SET
                day = ?,
                category = ?,
                title = ?,
                cost_plan = ?,
                cost_actual = ?
            WHERE id = ?
            """,
            (
                int(day),
                category,
                clean_title,
                float(cost_plan),
                float(cost_actual),
                expense_id,
            ),
        )


def delete_manual_expense(
    expense_id: int,
    trip_id: int,
    user_id: int,
):
    """Удаляет ручной расход, если он принадлежит пользователю."""
    with _conn() as connection:
        expense = connection.execute(
            """
            SELECT expenses.id
            FROM expenses
            INNER JOIN trips ON trips.id = expenses.trip_id
            WHERE expenses.id = ?
              AND expenses.trip_id = ?
              AND trips.user_id = ?
              AND expenses.is_manual = 1
            """,
            (expense_id, trip_id, user_id),
        ).fetchone()

        if not expense:
            raise ValueError(
                "Ручной расход не найден или недоступен для удаления."
            )

        connection.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,),
        )        
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

def add_manual_expense(
    trip_id: int,
    user_id: int,
    day: int,
    category: str,
    title: str,
    cost_plan: float,
    cost_actual: float,
):
    """
    Добавляет расход, который пользователь внёс вручную.

    Проверяет, что поездка принадлежит пользователю, и назначает
    новой записи следующий порядковый activity_idx.
    """
    clean_title = str(title).strip()

    if not clean_title:
        raise ValueError("Укажите название расхода.")

    with _conn() as connection:
        trip = connection.execute(
            """
            SELECT id
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()

        if not trip:
            raise ValueError("Поездка не найдена или недоступна.")

        last_index = connection.execute(
            """
            SELECT COALESCE(MAX(activity_idx), -1)
            FROM expenses
            WHERE trip_id = ? AND day = ?
            """,
            (trip_id, day),
        ).fetchone()[0]

        cursor = connection.execute(
            """
            INSERT INTO expenses(
                trip_id,
                day,
                activity_idx,
                category,
                title,
                cost_plan,
                cost_actual,
                is_manual
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                trip_id,
                int(day),
                int(last_index) + 1,
                category,
                clean_title,
                float(cost_plan),
                float(cost_actual),
            ),
        )

        return cursor.lastrowid
# ==========================================================
# ЧЕК-ЛИСТ ПОДГОТОВКИ К ПОЕЗДКЕ
# ==========================================================

def get_checklist_statuses(
    trip_id: int,
    user_id: int,
) -> dict[str, bool]:
    """
    Возвращает словарь отметок чек-листа конкретной поездки.

    Формат результата:
    {
        "checklist_12_abcdef123456": True,
        "checklist_12_987654321abc": False,
    }
    """
    with _conn() as connection:
        trip = connection.execute(
            """
            SELECT id
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()

        if not trip:
            raise ValueError("Поездка не найдена или недоступна.")

        rows = connection.execute(
            """
            SELECT item_key, is_completed
            FROM trip_checklist_items
            WHERE trip_id = ?
            """,
            (trip_id,),
        ).fetchall()

        return {
            str(row["item_key"]): bool(row["is_completed"])
            for row in rows
        }


def set_checklist_item_status(
    trip_id: int,
    user_id: int,
    item_key: str,
    is_completed: bool,
):
    """
    Создаёт или обновляет отметку одного пункта чек-листа.

    Проверяется, что поездка принадлежит текущему пользователю.
    """
    clean_item_key = str(item_key or "").strip()

    if not clean_item_key:
        raise ValueError("Не указан ключ пункта чек-листа.")

    with _conn() as connection:
        trip = connection.execute(
            """
            SELECT id
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()

        if not trip:
            raise ValueError("Поездка не найдена или недоступна.")

        connection.execute(
            """
            INSERT INTO trip_checklist_items(
                trip_id,
                item_key,
                is_completed,
                updated_at
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(trip_id, item_key)
            DO UPDATE SET
                is_completed = excluded.is_completed,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                trip_id,
                clean_item_key,
                int(bool(is_completed)),
            ),
        )


def reset_checklist(
    trip_id: int,
    user_id: int,
):
    """
    Снимает все отметки чек-листа конкретной поездки.

    Записи удаляются, поэтому при следующем открытии все пункты
    отображаются неотмеченными.
    """
    with _conn() as connection:
        trip = connection.execute(
            """
            SELECT id
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()

        if not trip:
            raise ValueError("Поездка не найдена или недоступна.")

        connection.execute(
            """
            DELETE FROM trip_checklist_items
            WHERE trip_id = ?
            """,
            (trip_id,),
        )
# ==========================================================
# РЕЖИМ «Я В ПОЕЗДКЕ»: ПОСЕЩЕНИЕ АКТИВНОСТЕЙ
# ==========================================================

def get_activity_visits(
    trip_id: int,
    user_id: int,
) -> dict[str, bool]:
    """Возвращает отметки посещения поездки текущего пользователя."""
    with _conn() as connection:
        trip = connection.execute(
            """
            SELECT id
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()

        if not trip:
            raise ValueError("Поездка не найдена или недоступна.")

        rows = connection.execute(
            """
            SELECT activity_key, is_visited
            FROM trip_activity_visits
            WHERE trip_id = ?
            """,
            (trip_id,),
        ).fetchall()

        return {
            str(row["activity_key"]): bool(row["is_visited"])
            for row in rows
        }


def set_activity_visit(
    trip_id: int,
    user_id: int,
    activity_key: str,
    is_visited: bool,
):
    """Создаёт или обновляет отметку посещения с проверкой владельца."""
    clean_key = str(activity_key or "").strip()

    if not clean_key:
        raise ValueError("Не указан ключ активности.")

    with _conn() as connection:
        trip = connection.execute(
            """
            SELECT id
            FROM trips
            WHERE id = ? AND user_id = ?
            """,
            (trip_id, user_id),
        ).fetchone()

        if not trip:
            raise ValueError("Поездка не найдена или недоступна.")

        connection.execute(
            """
            INSERT INTO trip_activity_visits(
                trip_id,
                activity_key,
                is_visited,
                updated_at
            )
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(trip_id, activity_key)
            DO UPDATE SET
                is_visited = excluded.is_visited,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                trip_id,
                clean_key,
                int(bool(is_visited)),
            ),
        )
# ==========================================================
# ТОЧЕЧНАЯ ЗАМЕНА АКТИВНОСТИ
# ==========================================================

def replace_trip_activity(
    trip_id: int,
    user_id: int,
    expected_data_json: str,
    day_index: int,
    activity_index: int,
    replacement: dict,
):
    """
    Атомарно заменяет одну активность.

    expected_data_json — исходное значение trip["data"], на основе
    которого пользователь запросил альтернативы.
    """
    import hashlib
    import json
    import math

    def money(value):
        if isinstance(value, bool):
            raise ValueError("Некорректная денежная сумма.")

        try:
            result = float(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValueError("Не удалось прочитать стоимость.") from error

        if not math.isfinite(result) or result < 0:
            raise ValueError("Стоимость должна быть числом не меньше нуля.")

        return round(result, 2)

    if not isinstance(replacement, dict):
        raise ValueError("Некорректная альтернатива.")

    with _conn() as connection:
        # Блокируем параллельную запись до завершения операции.
        connection.execute("BEGIN IMMEDIATE")

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

        if trip["data"] != expected_data_json:
            raise ValueError(
                "Маршрут уже изменился. Обновите страницу "
                "и запросите альтернативы заново."
            )

        route = json.loads(trip["data"])
        days = route.get("days")

        if (
            not isinstance(days, list)
            or isinstance(day_index, bool)
            or not isinstance(day_index, int)
            or not 0 <= day_index < len(days)
        ):
            raise ValueError("Выбранный день не найден.")

        day_data = days[day_index]

        if not isinstance(day_data, dict):
            raise ValueError("Некорректная структура дня.")

        activities = day_data.get("activities")

        if (
            not isinstance(activities, list)
            or isinstance(activity_index, bool)
            or not isinstance(activity_index, int)
            or not 0 <= activity_index < len(activities)
        ):
            raise ValueError("Выбранная активность не найдена.")

        original = activities[activity_index]

        if not isinstance(original, dict):
            raise ValueError("Некорректная исходная активность.")

        # Используем тот же алгоритм ключа, что и во вкладке
        # «Я в поездке»: день, дата, название, место, номер повтора.
        original_title = str(original.get("title") or "").strip()
        original_location = str(original.get("location") or "").strip()

        occurrence = sum(
            1
            for item in activities[:activity_index]
            if isinstance(item, dict)
            and str(item.get("title") or "").strip() == original_title
            and str(item.get("location") or "").strip() == original_location
        )

        visit_identity = {
            "day": str(day_data.get("day") or ""),
            "date": str(day_data.get("date") or "")[:10],
            "title": original_title,
            "location": original_location,
            "occurrence": occurrence,
        }

        visit_key = hashlib.sha256(
            json.dumps(
                visit_identity,
                ensure_ascii=False,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:24]

        visit = connection.execute(
            """
            SELECT is_visited
            FROM trip_activity_visits
            WHERE trip_id = ? AND activity_key = ?
            """,
            (trip_id, visit_key),
        ).fetchone()

        if visit and bool(visit["is_visited"]):
            raise ValueError(
                "Активность уже отмечена как посещённая. "
                "Сначала снимите отметку во вкладке «Я в поездке»."
            )

        # Ищем только плановую строку выбранной активности.
        expense_rows = connection.execute(
            """
            SELECT *
            FROM expenses
            WHERE trip_id = ?
              AND day = ?
              AND activity_idx = ?
              AND is_manual = 0
            """,
            (
                trip_id,
                day_data.get("day"),
                activity_index,
            ),
        ).fetchall()

        if len(expense_rows) > 1:
            raise ValueError(
                "Найдено несколько расходов для одной активности. "
                "Замена остановлена, чтобы не повредить данные."
            )

        expense = expense_rows[0] if expense_rows else None

        if expense:
            if (
                expense["title"] != original.get("title")
                or expense["category"] != original.get("type")
            ):
                raise ValueError(
                    "План расходов не соответствует маршруту. "
                    "Замена остановлена."
                )

            if money(expense["cost_actual"] or 0) > 0:
                raise ValueError(
                    "Для активности уже внесён фактический расход. "
                    "Заменять её нельзя."
                )

        original_type = str(original.get("type") or "").strip().upper()

        if original_type not in {"A", "F", "T", "S", "L", "H", "W"}:
            raise ValueError("Неизвестная категория исходной активности.")

        if replacement.get("type") != original_type:
            raise ValueError("При замене нельзя менять категорию активности.")

        clean_texts = {}

        for field, limit in (
            ("title", 200),
            ("location", 250),
            ("description", 500),
            ("tip", 500),
        ):
            value = replacement.get(field)

            if (
                not isinstance(value, str)
                or not value.strip()
                or len(value.strip()) > limit
            ):
                raise ValueError(
                    f"Некорректное поле альтернативы: {field}."
                )

            clean_texts[field] = value.strip()

        new_title_key = " ".join(clean_texts["title"].casefold().split())

        existing_titles = {
            " ".join(str(item.get("title") or "").casefold().split())
            for item in activities
            if isinstance(item, dict)
        }

        if new_title_key in existing_titles:
            raise ValueError(
                "Это место уже есть в плане выбранного дня."
            )

        old_cost = money(original.get("cost") or 0)
        new_cost = money(replacement.get("cost"))
        difference = round(new_cost - old_cost, 2)

        # Корректируем существующие итоги на разницу,
        # не пересобирая весь финансовый план.
        old_day_cost = money(
            day_data.get("day_cost")
            if day_data.get("day_cost") is not None
            else sum(
                money(item.get("cost") or 0)
                for item in activities
                if isinstance(item, dict)
            )
        )

        old_total_cost = money(
            route.get("total_cost")
            if route.get("total_cost") is not None
            else trip["budget"] or 0
        )

        new_day_cost = round(old_day_cost + difference, 2)
        new_total_cost = round(old_total_cost + difference, 2)

        if new_day_cost < 0 or new_total_cost < 0:
            raise ValueError(
                "Исходные суммы бюджета противоречат стоимости активности. "
                "Замена остановлена."
            )

        category_map = {
            "A": "activities",
            "F": "food",
            "T": "transport",
            "S": "accommodation",
            "L": "activities",
            "H": "other",
            "W": "activities",
        }

        breakdown = route.get("budget_breakdown")

        if not isinstance(breakdown, dict):
            raise ValueError(
                "В маршруте отсутствует структура бюджета."
            )

        budget_category = category_map[original_type]
        category_total = money(breakdown.get(budget_category) or 0)
        new_category_total = round(category_total + difference, 2)

        if new_category_total < 0:
            raise ValueError(
                "Сумма категории бюджета меньше необходимого уменьшения. "
                "Замена остановлена: исходный бюджет требует проверки."
            )

        # Остальные поля исходной активности сохраняем.
        new_activity = dict(original)
        new_activity.update(clean_texts)
        new_activity.update(
            {
                "type": original_type,
                "cost": new_cost,
                "time": original.get("time"),
                "duration_min": original.get("duration_min"),
                "lat": None,
                "lon": None,
            }
        )

        activities[activity_index] = new_activity
        day_data["day_cost"] = new_day_cost
        route["total_cost"] = new_total_cost
        breakdown[budget_category] = new_category_total

        connection.execute(
            """
            UPDATE trips
            SET data = ?, budget = ?
            WHERE id = ? AND user_id = ?
            """,
            (
                json.dumps(
                    route,
                    ensure_ascii=False,
                    allow_nan=False,
                ),
                new_total_cost,
                trip_id,
                user_id,
            ),
        )

        if expense:
            connection.execute(
                """
                UPDATE expenses
                SET category = ?, title = ?, cost_plan = ?
                WHERE id = ?
                """,
                (
                    original_type,
                    clean_texts["title"],
                    new_cost,
                    expense["id"],
                ),
            )
        else:
            connection.execute(
                """
                INSERT INTO expenses(
                    trip_id,
                    day,
                    activity_idx,
                    category,
                    title,
                    cost_plan,
                    cost_actual,
                    is_manual
                )
                VALUES (?, ?, ?, ?, ?, ?, NULL, 0)
                """,
                (
                    trip_id,
                    day_data.get("day"),
                    activity_index,
                    original_type,
                    clean_texts["title"],
                    new_cost,
                ),
            )

        # Старую непосещённую отметку больше не используем.
        connection.execute(
            """
            DELETE FROM trip_activity_visits
            WHERE trip_id = ? AND activity_key = ?
            """,
            (trip_id, visit_key),
        )
# Создание базы при импорте модуля.
init()
