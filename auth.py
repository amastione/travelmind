"""Регистрация, вход, выход и постоянная авторизация TravelMind."""
import hashlib
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import streamlit as st
from streamlit_cookies_controller import CookieController

import db


# Название cookie, в которой хранится токен текущей авторизации.
AUTH_COOKIE_NAME = "travelmind_auth_token"

# Время действия авторизации.
SESSION_DAYS = 30


def _cookie_controller() -> CookieController:
    """
    Создаёт контроллер browser-cookie.

    Нельзя использовать @st.cache_resource:
    CookieController создаёт Streamlit-компонент, а компоненты и виджеты
    запрещены внутри кэшируемых функций.
    """
    return CookieController()


def _hash(password: str) -> str:
    """Создаёт bcrypt-хэш пароля."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def _verify(password: str, pw_hash: str) -> bool:
    """Сверяет пароль с bcrypt-хэшем из базы."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        pw_hash.encode("utf-8"),
    )


def _token_hash(token: str) -> str:
    """
    Возвращает SHA-256-хэш токена.

    Сам токен находится только в cookie пользователя.
    В SQLite хранится исключительно его хэш.
    """
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def _get_cookie_token() -> Optional[str]:
    """Получает авторизационный токен из cookie браузера."""
    controller = _cookie_controller()
    token = controller.get(AUTH_COOKIE_NAME)

    if not token:
        return None

    return str(token)


def _set_cookie_token(token: str):
    """
    Записывает авторизационный токен в cookie на SESSION_DAYS дней.

    Важно:
    streamlit-cookies-controller ожидает параметр expires типа datetime,
    а не timestamp float.
    """
    controller = _cookie_controller()

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=SESSION_DAYS
    )

    controller.set(
        AUTH_COOKIE_NAME,
        token,
        expires=expires_at,
        path="/",
        secure=True,
        same_site="lax",
    )


def _delete_cookie_token():
    """Удаляет авторизационную cookie."""
    controller = _cookie_controller()

    try:
        controller.remove(AUTH_COOKIE_NAME)
    except Exception:
        # Если cookie уже нет, это не должно мешать выходу.
        pass


def restore_session() -> bool:
    """
    Восстанавливает вход после F5 / Ctrl+R / повторного открытия сайта.

    Если Streamlit session_state очищен:
    1. Берём токен из браузерной cookie;
    2. Хэшируем его;
    3. Ищем активную сессию в SQLite;
    4. Восстанавливаем user_id и username.
    """
    if "user_id" in st.session_state:
        return True

    token = _get_cookie_token()

    if not token:
        return False

    user = db.get_user_by_session_token(
        _token_hash(token)
    )

    if not user:
        # Сессия истекла, пользователь вышел или БД была очищена.
        _delete_cookie_token()
        return False

    st.session_state["user_id"] = int(user["id"])
    st.session_state["username"] = str(user["username"])
    st.session_state["auth_token"] = token

    return True


def register(username: str, password: str) -> Optional[str]:
    """
    Создаёт пользователя.

    Возвращает текст ошибки либо None, если регистрация прошла успешно.
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
    Выполняет вход:
    - проверяет логин и пароль;
    - создаёт сессию в SQLite на 30 дней;
    - сохраняет токен в cookie браузера.
    """
    user = db.get_user(username.strip())

    if not user or not _verify(password, user["password_hash"]):
        return "Неверный логин или пароль."

    # Безопасный непредсказуемый токен.
    raw_token = secrets.token_urlsafe(48)

    # В БД сохраняем не токен, а только его хэш.
    token_hash = _token_hash(raw_token)

    # Время хранения сессии в SQLite — Unix timestamp.
    expires_at = int(
        time.time() + SESSION_DAYS * 24 * 60 * 60
    )

    db.create_auth_session(
        user_id=int(user["id"]),
        token_hash=token_hash,
        expires_at=expires_at,
    )

    # Текущая сессия Streamlit.
    st.session_state["user_id"] = int(user["id"])
    st.session_state["username"] = str(user["username"])
    st.session_state["auth_token"] = raw_token

    # Постоянная сессия браузера.
    _set_cookie_token(raw_token)

    return None


def remember_trip(trip_id: int):
    """Запоминает открытую поездку в текущей сессии Streamlit."""
    st.session_state["current_trip_id"] = int(trip_id)


def logout():
    """
    Выполняет выход:
    - отключает токен в SQLite;
    - удаляет токен из cookie;
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
    """Защищает внутренние страницы и восстанавливает сессию при F5."""
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
    """Выводит кнопку возврата на главную страницу справа сверху."""
    spacer, menu_column = st.columns([4.6, 1.8])

    with menu_column:
        st.page_link(
            "app.py",
            label="⌂ Главное меню",
            use_container_width=True,
        )
