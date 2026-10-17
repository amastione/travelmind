"""Общий пароль для доступа к закрытой бета-версии TravelMind."""

import hashlib
import hmac

import streamlit as st


# Версия доступа. Если изменить её, все старые ссылки доступа
# перестанут работать, и пользователям нужно будет ввести код заново.
ACCESS_VERSION = "2026-10-18-v3"

# Имя служебного параметра в URL.
ACCESS_QUERY_PARAM = "tm_beta"


def get_secret(name: str) -> str:
    """Получает обязательное значение из Streamlit Secrets."""
    try:
        return str(st.secrets[name])
    except KeyError:
        st.error(
            f"В Streamlit Secrets отсутствует настройка: {name}"
        )
        st.stop()


def get_query_param(name: str) -> str:
    """Безопасно получает одно значение query-параметра."""
    value = st.query_params.get(name, "")

    if isinstance(value, list):
        return str(value[0]) if value else ""

    return str(value)


def set_query_param(name: str, value: str) -> None:
    """Записывает один query-параметр в URL."""
    st.query_params[name] = str(value)


def remove_query_param(name: str) -> None:
    """Удаляет query-параметр из URL."""
    try:
        del st.query_params[name]
    except KeyError:
        pass


def create_access_token() -> str:
    """
    Создаёт подписанный маркер доступа.

    В URL попадёт не пароль, а строка вида:
    версия.подпись
    """
    secret = get_secret("SITE_ACCESS_COOKIE_PASSWORD")

    signature = hmac.new(
        secret.encode("utf-8"),
        ACCESS_VERSION.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{ACCESS_VERSION}.{signature}"


def has_site_access() -> bool:
    """Проверяет доступ из текущей сессии или подписанного URL."""
    if (
        st.session_state.get("site_access_granted") is True
        and st.session_state.get("site_access_version")
        == ACCESS_VERSION
    ):
        return True

    saved_token = get_query_param(ACCESS_QUERY_PARAM)
    expected_token = create_access_token()

    if saved_token and hmac.compare_digest(
        saved_token,
        expected_token,
    ):
        st.session_state["site_access_granted"] = True
        st.session_state["site_access_version"] = ACCESS_VERSION
        return True

    return False


def sync_access_to_url() -> None:
    """
    Сохраняет подтверждение доступа в URL.

    Не удаляет tm_auth и tm_trip, которые используются auth.py.
    """
    expected_token = create_access_token()

    if get_query_param(ACCESS_QUERY_PARAM) != expected_token:
        set_query_param(
            ACCESS_QUERY_PARAM,
            expected_token,
        )


def render_access_styles() -> None:
    """Подключает стили для страницы ввода кода."""
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(
                    circle at 12% 12%,
                    rgba(34, 211, 238, 0.16),
                    transparent 30%
                ),
                radial-gradient(
                    circle at 90% 85%,
                    rgba(139, 92, 246, 0.18),
                    transparent 35%
                ),
                linear-gradient(
                    135deg,
                    #070B14 0%,
                    #0D1628 52%,
                    #101426 100%
                );
        }

        [data-testid="stForm"] {
            padding: 1.65rem;
            border: 1px solid rgba(103, 232, 249, 0.26);
            border-radius: 22px;
            background:
                linear-gradient(
                    135deg,
                    rgba(17, 30, 53, 0.86),
                    rgba(14, 22, 43, 0.84)
                );
        }

        .tm-access-card {
            max-width: 560px;
            margin: 7vh auto 1.2rem;
            text-align: center;
        }

        .tm-access-icon {
            font-size: 3rem
