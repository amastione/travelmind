"""Регистрация, вход, выход и защита страниц TravelMind."""
from typing import Optional

import bcrypt
import streamlit as st

import db


def _hash(password: str) -> str:
    """Превращает пароль в необратимый bcrypt-хэш."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, pw_hash: str) -> bool:
    """Проверяет введённый пароль по сохранённому bcrypt-хэшу."""
    return bcrypt.checkpw(password.encode(), pw_hash.encode())


def restore_session() -> bool:
    """
    Совместимая заглушка восстановления сессии.

    Ранее здесь использовалась устаревшая библиотека
    streamlit-cookies-manager, несовместимая с текущим Streamlit.
    Функция сохранена, чтобы app.py и страницы не падали.
    """
    return "user_id" in st.session_state


def register(username: str, password: str) -> Optional[str]:
    """
    Создаёт пользователя.

    Возвращает текст ошибки либо None при успешной регистрации.
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
    Проверяет логин и пароль, затем открывает сессию пользователя.
    """
    user = db.get_user(username.strip())

    if not user or not _verify(password, user["password_hash"]):
        return "Неверный логин или пароль."

    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]

    return None


def remember_trip(trip_id: int):
    """
    Запоминает открытую поездку внутри активной Streamlit-сессии.
    """
    st.session_state["current_trip_id"] = int(trip_id)


def logout():
    """Очищает данные активной сессии пользователя."""
    for key in (
        "user_id",
        "username",
        "auth_token",
        "current_trip_id",
        "last_trip_id",
    ):
        st.session_state.pop(key, None)


def require_auth() -> int:
    """Защищает внутренние страницы от неавторизованного доступа."""
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
    Выводит компактную кнопку возврата в главное меню справа сверху.

    Добавляйте вызов этой функции сразу после подключения CSS
    на каждой внутренней странице.
    """
    spacer, menu_column = st.columns([4.8, 1.7])

    with menu_column:
        st.page_link(
            "app.py",
            label="⌂ Главное меню",
            use_container_width=True,
        )
