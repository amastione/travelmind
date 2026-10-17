"""Общий пароль для доступа к закрытой бета-версии TravelMind."""

import hashlib
import hmac

import streamlit as st


# ==========================================================
# НАСТРОЙКИ ЗАКРЫТОГО ДОСТУПА
# ==========================================================
#
# Обязательные параметры в Streamlit Secrets:
#
# SITE_ACCESS_PASSWORD = "пароль_закрытой_беты"
# SITE_ACCESS_COOKIE_PASSWORD = "длинная_случайная_секретная_строка"
#
# SITE_ACCESS_COOKIE_PASSWORD используется только для создания
# криптографической подписи. Пользователь его не вводит.
#
# Чтобы отозвать доступ у всех бета-тестеров:
# 1. Измените ACCESS_VERSION.
# 2. Сделайте Commit changes в GitHub.
#
# После этого старые подтверждения доступа перестанут работать.
# ==========================================================

ACCESS_VERSION = "2026-10-18-v2"

# Название служебного параметра в URL.
# Он не содержит мастер-пароль.
ACCESS_QUERY_PARAM = "tm_beta"


def _get_secret(name: str) -> str:
    """Получает обязательное значение из Streamlit Secrets."""
    try:
        return str(st.secrets[name])
    except KeyError:
        st.error(
            f"В Streamlit Secrets отсутствует параметр: `{name}`."
        )
        st.stop()


def _get_query_value(name: str) -> str:
    """Безопасно получает один параметр из URL."""
    value = st.query_params.get(name)

    if isinstance(value, list):
        value = value[0] if value else ""

    return str(value or "")


def _set_query_value(name: str, value: str) -> None:
    """Создаёт или обновляет конкретный параметр URL."""
    st.query_params[name] = str(value)


def _remove_query_value(name: str) -> None:
    """Удаляет конкретный параметр URL."""
    try:
        del st.query_params[name]
    except KeyError:
        pass


def _create_access_token() -> str:
    """
    Создаёт подписанный маркер доступа.

    В URL записывается:
    ACCESS_VERSION.HMAC_SHA256_SIGNATURE

    Мастер-пароль в URL не записывается.
    """
    signing_secret = _get_secret("SITE_ACCESS_COOKIE_PASSWORD")

    signature = hmac.new(
        signing_secret.encode("utf-8"),
        ACCESS_VERSION.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{ACCESS_VERSION}.{signature}"


def _access_is_current() -> bool:
    """
    Проверяет бета-доступ:

    1. В session_state — во время работы текущей сессии.
    2. В URL — после F5 или нового запуска Streamlit-сессии.
    """
    if (
        st.session_state.get("site_access_granted") is True
        and st.session_state.get("site_access_version")
        == ACCESS_VERSION
    ):
        return True

    saved_token = _get_query_value(ACCESS_QUERY_PARAM)
    expected_token = _create_access_token()

    if saved_token and hmac.compare_digest(
        saved_token,
        expected_token,
    ):
        st.session_state["site_access_granted"] = True
        st.session_state["site_access_version"] = ACCESS_VERSION
        return True

    return False


def _sync_access_to_url() -> None:
    """
    Сохраняет подписанное подтверждение в URL.

    Не удаляет другие параметры, нужные auth.py:
    - tm_auth — пользовательская авторизация;
    - tm_trip — текущая открытая поездка.
    """
    expected_token = _create_access_token()

    if _get_query_value(ACCESS_QUERY_PARAM) != expected_token:
        _set_query_value(
            ACCESS_QUERY_PARAM,
            expected_token,
        )


def _render_access_styles() -> None:
    """Подключает стили для страницы закрытой беты."""
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

        [data-testid="stHeader"] {
            background: transparent !important;
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
            box-shadow:
                0 20px 60px rgba(0, 0, 0, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }

        .tm-access-card {
            margin: 7vh auto 1.2rem;
            max-width: 560px;
            text-align: center;
        }

        .tm-access-icon {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 76px;
            height: 76px;
            margin-bottom: 1rem;
            border: 1px solid rgba(103, 232, 249, 0.36);
            border-radius: 24px;
            background:
                linear-gradient(
                    135deg,
                    rgba(6, 182, 212, 0.25),
                    rgba(139, 92, 246, 0.26)
                );
            color: #FFFFFF;
            font-size: 2rem;
            box-shadow: 0 12px 26px rgba(34, 211, 238, 0.15);
        }

        .tm-access-title {
            margin: 0;
            color: #F8FAFC;
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.05rem;
        }

        .tm-access-text {
            margin: 0.75rem auto 0;
            max-width: 480px;
            color: #B6C6DB;
            font-size: 1rem;
            line-height: 1.65;
        }

        [data-testid="stWidgetLabel"] p {
            color: #D6E0EF !important;
            font-weight: 650 !important;
        }

        .stTextInput input {
            min-height: 50px !important;
            border: 1px solid rgba(148, 163, 184, 0.36) !important;
            border-radius: 12px !important;
            background: rgba(7, 13, 26, 0.78) !important;
            color: #F8FAFC !important;
        }

        .stTextInput input:focus {
            border-color: rgba(34, 211, 238, 0.85) !important;
            box-shadow: 0 0 0 2px rgba(34, 211, 238, 0.13) !important;
        }

        .stFormSubmitButton > button {
            width: 100%;
            min-height: 50px;
            border: 0 !important;
            border-radius: 13px !important;
            background:
                linear-gradient(
                    135deg,
                    #06B6D4 0%,
                    #22D
