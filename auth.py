"""Регистрация, вход, выход и постоянная авторизация TravelMind."""
import hashlib
import secrets
import time
from typing import Optional

import bcrypt
import streamlit as st

import db


# Название параметра в URL, содержащего токен текущей сессии.
AUTH_QUERY_PARAM = "tm_session"

# Срок действия сессии: 30 дней.
SESSION_DAYS = 30


def _hash(password: str) -> str:
    """Превращает пароль в необратимый bcrypt-хэш."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, pw_hash: str) -> bool:
    """Проверяет введённый пароль по bcrypt-хэшу."""
    return bcrypt.checkpw(password.encode(), pw_hash.encode())


def _token_hash(token: str) -> str:
    """
    Создаёт SHA-256-хэш токена.

    В базе хранится только хэш, а не исходный токен. Поэтому сам токен
    нельзя восстановить даже при прямом доступе к файлу базы данных.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_url_token() -> Optional[str]:
    """Получает токен авторизации из параметров URL."""
    token = st.query_params.get(AUTH_QUERY_PARAM)

    if isinstance(token, list):
        token = token[0] if token else None

    if not token:
        return None

    return str(token)


def _set_url_token(token: str):
    """
    Добавляет токен авторизации в URL.

    Streamlit сохраняет этот параметр при обычной перезагрузке страницы.
    """
    st.query_params[AUTH_QUERY_PARAM] = token


def _remove_url_token():
    """Удаляет токен из URL после выхода пользователя."""
    try:
        del st.query_params[AUTH_QUERY_PARAM]
    except KeyError:
        pass


def restore_session() -> bool:
    """
    Восстанавливает авторизацию после обновления страницы.

    Логика:
    1. Если сессия Streamlit ещё существует — просто убеждаемся,
       что токен есть в URL.
    2. Если браузер обновлён, session_state пустой:
       читаем токен из URL и проверяем его в SQLite.
    """
    # Обычное переключение между страницами Streamlit.
    # session_state ещё существует, но query-параметры могли очиститься.
    if "user_id" in st.session_state:
        token = st.session_state.get("auth_token")

        if token and _get_url_token() != token:
            _set_url_token(token)

        return True

    # Полная перезагрузка: восстанавливаем вход по URL-токену.
    token = _get_url_token()

    if not token:
        return False

    user = db.get_user_by_session_token(_token_hash(token))

    if not user:
        _remove_url_token()
        return False

    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.session_state["auth_token"] = token

    return True


def register(username: str, password: str) -> Optional[str]:
    """
    Создаёт пользователя.

    Возвращает текст ошибки или None при успешной регистрации.
    """
    username = username.strip()

    if len(username) < 3:
        return "Логин должен быть не короче 3 символов."

    if len(password) < 6:
        return "Пароль должен быть не короче 6 символов."

    if db.get_user(username):
        return "Такой логин уже занят."

    db.create_user(username, _hash(password))
    return None


def login(username: str, password: str) -> Optional[str]:
    """
    Проверяет пользователя, создаёт постоянную сессию в БД
    и записывает токен в URL.
    """
    user = db.get_user(username.strip())

    if not user or not _verify(password, user["password_hash"]):
        return "Неверный логин или пароль."

    # Создаём достаточно длинный криптографически стойкий токен.
    raw_token = secrets.token_urlsafe(48)

    # Сохраняем только хэш токена.
    token_hash = _token_hash(raw_token)

    # Время истечения токена в Unix timestamp.
    expires_at = int(
        time.time() + SESSION_DAYS * 24 * 60 * 60
    )

    db.create_auth_session(
        user_id=int(user["id"]),
        token_hash=token_hash,
        expires_at=expires_at,
    )

    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.session_state["auth_token"] = raw_token

    # Благодаря этому токен переживёт F5 / Ctrl+R.
    _set_url_token(raw_token)

    return None


def remember_trip(trip_id: int):
    """Запоминает открытую поездку в текущей Streamlit-сессии."""
    st.session_state["current_trip_id"] = int(trip_id)


def logout():
    """
    Завершает сессию:
    - удаляет токен из БД;
    - удаляет токен из URL;
    - очищает session_state.
    """
    token = st.session_state.get("auth_token") or _get_url_token()

    if token:
        db.delete_auth_session(_token_hash(token))

    _remove_url_token()

    for key in (
        "user_id",
        "username",
        "auth_token",
        "current_trip_id",
        "last_trip_id",
    ):
        st.session_state.pop(key, None)


def require_auth() -> int:
    """Не пускает на внутренние страницы без авторизации."""
    restore_session()

    if "user_id" not in st.session_state:
        st.warning("Для доступа войдите в систему.")

        st.page_link(
            "app.py",
            label="⌂ Перейти на главную страницу",
            use_container_width=True,
        )

        st.stop()

    return int(st.session_state["user_id"])


def render_main_menu_button():
    """
    Отображает заметную кнопку возврата в главное меню.

    Стили кнопки задаются CSS на соответствующей странице.
    """
    spacer, menu_column = st.columns([4.6, 1.8])

    with menu_column:
        st.page_link(
            "app.py",
            label="⌂ Главное меню",
            use_container_width=True,
        )
