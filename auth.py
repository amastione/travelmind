"""Регистрация, вход, выход. Пароли хэшируются через bcrypt."""
from typing import Optional

import bcrypt
import streamlit as st

import db


def _hash(password: str) -> str:
    """Превращает пароль в необратимую строку-хэш."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, pw_hash: str) -> bool:
    """Сверяет введённый пароль с сохранённым хэшем."""
    return bcrypt.checkpw(password.encode(), pw_hash.encode())


def register(username: str, password: str) -> Optional[str]:
    """Создаёт пользователя. Возвращает текст ошибки или None, если всё ок."""
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
    """Проверяет пароль и открывает сессию."""
    user = db.get_user(username.strip())
    if not user or not _verify(password, user["password_hash"]):
        return "Неверный логин или пароль."
    st.session_state["user_id"] = user["id"]
    st.session_state["username"] = user["username"]
    return None


def logout():
    """Закрывает сессию."""
    for key in ("user_id", "username", "current_trip_id", "last_trip_id"):
        st.session_state.pop(key, None)


def require_auth() -> int:
    """Защита страниц: без входа дальше не пускаем."""
    if "user_id" not in st.session_state:
        st.warning("Для доступа войдите в систему.")
        st.page_link("app.py", label="К странице входа →")
        st.stop()
    return st.session_state["user_id"]
