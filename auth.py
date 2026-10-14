"""Регистрация, вход, выход и постоянная авторизация TravelMind."""
import hashlib
import secrets
import time
from typing import Optional

import bcrypt
import streamlit as st
from streamlit_cookies_controller import CookieController

import db


# Имя cookie, в которой хранится случайный токен авторизации.
AUTH_COOKIE_NAME = "travelmind_auth_token"

# Авторизация действует 30 дней.
SESSION_DAYS = 30


def _cookie_controller() -> CookieController:
    """
    Создаёт контроллер cookie.

    Нельзя применять @st.cache_resource или @st.cache_data:
    CookieController использует Streamlit-компонент, аналогичный виджету,
    а виджеты внутри кэшируемых функций запрещены.
    """
    return CookieController()


def _hash(password: str) -> str:
    """Создаёт необратимый bcrypt-хэш пароля."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )


def _verify(password: str, pw_hash: str) -> bool:
    """Проверяет пароль по bcrypt-хэшу."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        pw_hash.encode("utf-8"),
    )


def _token_hash(token: str) -> str:
    """
    Хэширует токен для хранения в SQLite.

    Исходный токен не сохраняется в базе: в БД остаётся только SHA-256-хэш.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_cookie_token() -> Optional[str]:
    """Получает токен текущего пользователя из браузерной cookie."""
    controller = _cookie_controller()
    token = controller.get(AUTH_COOKIE_NAME)

    if not token:
        return None

    return str(token)


def _set_cookie_token(token: str):
    """Сохраняет токен в браузерной cookie на 30 дней."""
    controller = _cookie_controller()

    expires_at = time.time() + SESSION_DAYS * 24 * 60 * 60

    controller.set(
        AUTH_COOKIE_NAME,
        token,
        expires=expires_at,
    )


def _delete_cookie_token():
    """Удаляет токен авторизации из cookie браузера."""
    controller = _cookie_controller()

    try:
        controller.remove(AUTH_COOKIE_NAME)
    except Exception:
        # Если cookie уже нет, выход всё равно должен завершиться корректно.
        pass


def restore_session() -> bool:
    """
    Восстанавливает вход после перезагрузки страницы.

    Если session_state очищен после F5 / Ctrl+R:
    1. Берём токен из cookie;
    2. Ищем хэш токена в SQLite;
    3. Восстанавливаем user_id и username.
    """
    if "user_id" in st.session_state:
        return True

    token = _get_cookie_token()

    if not token:
        return False

    user = db.get_user_by_session_token(_token_hash(token))

    if not user:
        # Токен истёк, пользователь вышел ранее или БД была очищена.
        _delete_cookie_token()
        return False

    st.session_state["user_id"] = int(user["id"])
    st.session_state["username"] = str(user["username"])
    st.session_state["auth_token"] = token

    return True


def register(username: str, password: str) -> Optional[str]:
    """
    Создаёт пользователя.

    Возвращает текст ошибки или None, если регистрация успешна.
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
    Проверяет пароль, создаёт сессию в SQLite и сохраняет токен в cookie.
    """
    user = db.get_user(username.strip())

    if not user or not _verify(password, user["password_hash"]):
        return "Неверный логин или пароль."

    # Генерируем криптографически стойкий токен.
    raw_token = secrets.token_urlsafe(48)

    # В SQLite храним только хэш токена.
    token_hash = _token_hash(raw_token)

    expires_at = int(
        time.time() + SESSION_DAYS * 24 * 60 * 60
    )

    db.create_auth_session(
        user_id=int(user["id"]),
        token_hash=token_hash,
        expires_at=expires_at,
    )

    st.session_state["user_id"] = int(user["id"])
    st.session_state["username"] = str(user["username"])
    st.session_state["auth_token"] = raw_token

    # Cookie переживёт F5, Ctrl+R, переходы между страницами
    # и повторное открытие браузера.
    _set_cookie_token(raw_token)

    return None


def remember_trip(trip_id: int):
    """Запоминает ID открытой поездки в текущей сессии."""
    st.session_state["current_trip_id"] = int(trip_id)


def logout():
    """
    Завершает сессию:
    - удаляет токен из SQLite;
    - удаляет cookie браузера;
    - очищает session_state.
    """
    token = st.session_state.get("auth_token")

    if not token:
        token = _get_cookie_token()

    if token:
        db.delete_auth_session(_token_hash(token))

    _delete_cookie_token()

    for key in (
        "user_id",
        "username",
        "auth_token",
        "current_trip_id",
        "last_trip_id",
    ):
        st.session_state.pop(key, None)


def require_auth() -> int:
    """Проверяет вход пользователя на внутренних страницах."""
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
    """Выводит яркую кнопку возврата в главное меню справа сверху."""
    spacer, menu_column = st.columns([4.6, 1.8])

    with menu_column:
        st.page_link(
            "app.py",
            label="⌂ Главное меню",
            use_container_width=True,
        )
