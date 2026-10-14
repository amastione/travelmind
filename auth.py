"""Регистрация, вход, выход и постоянная авторизация TravelMind."""
import hashlib
import secrets
import time
from typing import Optional

import bcrypt
import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager

import db


COOKIE_AUTH_TOKEN = "travelmind_auth_token"
COOKIE_TRIP_ID = "travelmind_last_trip_id"
SESSION_DAYS = 30


def _get_cookie_manager() -> EncryptedCookieManager:
    """
    Возвращает менеджер защищённых cookie.

    COOKIE_PASSWORD используется для шифрования значений cookie.
    Его нужно указать в Streamlit Secrets.
    """
    cookie_password = st.secrets.get("COOKIE_PASSWORD")

    if not cookie_password:
        st.error(
            "Не настроен COOKIE_PASSWORD. Добавьте его в Streamlit Secrets, "
            "чтобы работала постоянная авторизация."
        )
        st.stop()

    cookies = EncryptedCookieManager(
        prefix="travelmind/",
        password=cookie_password,
    )

    if not cookies.ready():
        st.stop()

    return cookies


def _hash(password: str) -> str:
    """Превращает пароль в необратимую строку-хэш."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, pw_hash: str) -> bool:
    """Сверяет введённый пароль с сохранённым хэшем."""
    return bcrypt.checkpw(password.encode(), pw_hash.encode())


def _token_hash(token: str) -> str:
    """
    Хэширует токен перед сохранением в БД.

    В базе не хранится исходный токен. Даже при доступе к SQLite-файлу
    злоумышленник не сможет использовать хэш как ключ входа.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _save_cookie(cookies, key: str, value: str):
    """Сохраняет значение в защищённую cookie."""
    cookies[key] = value
    cookies.save()


def _delete_cookie(cookies, key: str):
    """Удаляет cookie без ошибки, если её уже нет."""
    try:
        del cookies[key]
    except KeyError:
        pass

    cookies.save()


def restore_session() -> bool:
    """
    Восстанавливает авторизацию после обновления страницы.

    Сначала проверяет session_state. Если его нет, берёт токен из cookie,
    проверяет его в базе и возвращает пользователя в активную сессию.
    """
    if "user_id" in st.session_state:
        return True

    cookies = _get_cookie_manager()
    token = cookies.get(COOKIE_AUTH_TOKEN)

    if not token:
        return False

    user = db.get_user_by_session_token(_token_hash(token))

    if not user:
        _delete_cookie(cookies, COOKIE_AUTH_TOKEN)
        _delete_cookie(cookies, COOKIE_TRIP_ID)
        return False

    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.session_state["auth_token"] = token

    # Восстанавливаем последнюю открытую поездку.
    # Это позволяет оставаться на странице маршрута после F5.
    trip_id_value = cookies.get(COOKIE_TRIP_ID)

    if trip_id_value:
        try:
            st.session_state["current_trip_id"] = int(trip_id_value)
        except (TypeError, ValueError):
            _delete_cookie(cookies, COOKIE_TRIP_ID)

    return True


def register(username: str, password: str) -> Optional[str]:
    """Создаёт пользователя. Возвращает ошибку или None."""
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
    Проверяет пароль, создаёт постоянную сессию и сохраняет токен в cookie.
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
        user_id=user["id"],
        token_hash=token_hash,
        expires_at=expires_at,
    )

    cookies = _get_cookie_manager()
    _save_cookie(cookies, COOKIE_AUTH_TOKEN, raw_token)

    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    st.session_state["auth_token"] = raw_token

    return None


def remember_trip(trip_id: int):
    """
    Сохраняет текущую поездку в session_state и cookie.

    Благодаря этому при перезагрузке страницы маршрута пользователь
    возвращается именно к последней открытой поездке.
    """
    st.session_state["current_trip_id"] = int(trip_id)

    cookies = _get_cookie_manager()
    _save_cookie(cookies, COOKIE_TRIP_ID, str(trip_id))


def logout():
    """Закрывает сессию: удаляет токен из БД, cookie и session_state."""
    cookies = _get_cookie_manager()
    token = st.session_state.get("auth_token") or cookies.get(
        COOKIE_AUTH_TOKEN
    )

    if token:
        db.delete_auth_session(_token_hash(token))

    _delete_cookie(cookies, COOKIE_AUTH_TOKEN)
    _delete_cookie(cookies, COOKIE_TRIP_ID)

    for key in (
        "user_id",
        "username",
        "auth_token",
        "current_trip_id",
        "last_trip_id",
    ):
        st.session_state.pop(key, None)


def require_auth() -> int:
    """Защита внутренних страниц и автоматическое восстановление сессии."""
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
    Рисует кнопку возврата на главную страницу.

    Вызывается на каждой внутренней странице после подключения CSS.
    """
    left, right = st.columns([5, 1.65])

    with right:
        st.page_link(
            "app.py",
            label="⌂ Главное меню",
            use_container_width=True,
        )
