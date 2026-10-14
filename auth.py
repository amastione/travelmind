"""Регистрация, вход, выход и постоянная авторизация TravelMind."""
import hashlib
import secrets
import time
from typing import Optional

import bcrypt
import streamlit as st

import db


# Параметры URL.
# tm_auth — токен текущей авторизации.
# tm_trip — ID последней открытой поездки.
AUTH_QUERY_PARAM = "tm_auth"
TRIP_QUERY_PARAM = "tm_trip"

# Срок действия записи сессии в SQLite.
SESSION_DAYS = 30


def _hash(password: str) -> str:
    """Создаёт необратимый bcrypt-хэш пароля."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def _verify(password: str, pw_hash: str) -> bool:
    """Проверяет пароль по bcrypt-хэшу."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        pw_hash.encode("utf-8"),
    )


def _token_hash(token: str) -> str:
    """
    Хэширует токен для хранения в SQLite.

    Исходный секретный токен в БД не записывается.
    """
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def _get_query_value(name: str) -> Optional[str]:
    """Безопасно читает один query-параметр URL."""
    value = st.query_params.get(name)

    if isinstance(value, list):
        value = value[0] if value else None

    if not value:
        return None

    return str(value)


def _set_query_value(name: str, value: str):
    """Устанавливает один параметр URL."""
    st.query_params[name] = str(value)


def _remove_query_value(name: str):
    """Удаляет параметр URL, если он существует."""
    try:
        del st.query_params[name]
    except KeyError:
        pass


def _restore_trip_from_url():
    """
    Восстанавливает ID текущей поездки из URL.

    Это нужно, чтобы при F5 на странице маршрута не появлялось
    сообщение «Поездка не выбрана».
    """
    trip_id = _get_query_value(TRIP_QUERY_PARAM)

    if not trip_id:
        return

    try:
        st.session_state["current_trip_id"] = int(trip_id)
    except (TypeError, ValueError):
        _remove_query_value(TRIP_QUERY_PARAM)


def _sync_session_to_url():
    """
    Записывает токен и открытую поездку в URL.

    При переходе между страницами Streamlit иногда очищает query-параметры,
    поэтому эта функция вызывается на каждой защищённой странице.
    """
    token = st.session_state.get("auth_token")

    if token and _get_query_value(AUTH_QUERY_PARAM) != token:
        _set_query_value(AUTH_QUERY_PARAM, token)

    trip_id = st.session_state.get("current_trip_id")

    if trip_id is not None:
        _set_query_value(TRIP_QUERY_PARAM, str(trip_id))


def restore_session() -> bool:
    """
    Восстанавливает авторизацию после F5 / Ctrl+R.

    Сценарий 1: Streamlit-сессия ещё жива.
    Тогда синхронизируем токен с URL.

    Сценарий 2: после обновления session_state очищен.
    Берём токен из URL, проверяем в SQLite и восстанавливаем пользователя.
    """
    if "user_id" in st.session_state:
        _sync_session_to_url()
        _restore_trip_from_url()
        return True

    token = _get_query_value(AUTH_QUERY_PARAM)

    if not token:
        return False

    user = db.get_user_by_session_token(
        _token_hash(token)
    )

    if not user:
        _remove_query_value(AUTH_QUERY_PARAM)
        _remove_query_value(TRIP_QUERY_PARAM)
        return False

    st.session_state["user_id"] = int(user["id"])
    st.session_state["username"] = str(user["username"])
    st.session_state["auth_token"] = token

    _restore_trip_from_url()
    _sync_session_to_url()

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
    Выполняет вход:
    1. Проверяет логин и пароль.
    2. Создаёт токен авторизации.
    3. Сохраняет хэш токена в SQLite.
    4. Добавляет токен в URL, чтобы пережить обновление страницы.
    """
    user = db.get_user(username.strip())

    if not user or not _verify(password, user["password_hash"]):
        return "Неверный логин или пароль."

    raw_token = secrets.token_urlsafe(48)
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

    # Ключевой момент: токен сохраняется в URL до st.rerun().
    _set_query_value(AUTH_QUERY_PARAM, raw_token)

    return None


def remember_trip(trip_id: int):
    """
    Запоминает текущую поездку и добавляет её ID в URL.
    """
    st.session_state["current_trip_id"] = int(trip_id)
    _set_query_value(TRIP_QUERY_PARAM, str(trip_id))
    _sync_session_to_url()


def logout():
    """
    Выполняет выход:
    - деактивирует сессию в SQLite;
    - удаляет токен и ID маршрута из URL;
    - очищает данные текущей Streamlit-сессии.
    """
    token = (
        st.session_state.get("auth_token")
        or _get_query_value(AUTH_QUERY_PARAM)
    )

    if token:
        db.delete_auth_session(_token_hash(token))

    _remove_query_value(AUTH_QUERY_PARAM)
    _remove_query_value(TRIP_QUERY_PARAM)

    for key in (
        "user_id",
        "username",
        "auth_token",
        "current_trip_id",
        "last_trip_id",
    ):
        st.session_state.pop(key, None)


def require_auth() -> int:
    """
    Защищает внутренние страницы и автоматически восстанавливает вход.
    """
    restore_session()

    if "user_id" not in st.session_state:
        st.warning("Для доступа войдите в систему.")

        st.page_link(
            "app.py",
            label="⌂ Перейти на главную страницу",
            use_container_width=True,
        )

        st.stop()

    # При любом открытии защищённой страницы токен снова синхронизируется.
    _sync_session_to_url()

    return int(st.session_state["user_id"])


def render_main_menu_button():
    """Выводит яркую кнопку возврата на главную страницу."""
    spacer, menu_column = st.columns([4.6, 1.8])

    with menu_column:
        st.page_link(
            "app.py",
            label="⌂ Главное меню",
            use_container_width=True,
        )
