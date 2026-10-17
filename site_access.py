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
# SITE_ACCESS_COOKIE_PASSWORD используется как секрет для подписи
# доступа. Пользователь его НЕ вводит и в URL он НЕ попадает.
#
# Чтобы отозвать доступ у всех бета-тестеров:
# 1. Измените ACCESS_VERSION.
# 2. Сделайте Commit changes в GitHub.
#
# После нового развёртывания ранее выданные ссылки доступа
# станут недействительными.
# ==========================================================

ACCESS_VERSION = "2026-10-18-v1"

# Название параметра доступа в URL.
# В нём хранится не пароль, а подписанный служебный токен.
ACCESS_QUERY_PARAM = "tm_beta"


def _get_secret(name: str) -> str:
    """Возвращает обязательный параметр из Streamlit Secrets."""
    try:
        return str(st.secrets[name])
    except KeyError:
        st.error(
            f"В Streamlit Secrets отсутствует параметр: `{name}`. "
            "Проверьте настройки приложения."
        )
        st.stop()


def _get_query_value(name: str) -> str:
    """Безопасно читает одиночный параметр из URL."""
    value = st.query_params.get(name)

    if isinstance(value, list):
        value = value[0] if value else ""

    return str(value or "")


def _set_query_value(name: str, value: str) -> None:
    """Добавляет или обновляет один параметр URL."""
    st.query_params[name] = str(value)


def _remove_query_value(name: str) -> None:
    """Удаляет параметр URL, если он существует."""
    try:
        del st.query_params[name]
    except KeyError:
        pass


def _create_access_token() -> str:
    """
    Создаёт подписанный токен доступа.

    Формат токена:
    ACCESS_VERSION.HMAC_SHA256_SIGNATURE

    В нём нет общего пароля. Без SITE_ACCESS_COOKIE_PASSWORD
    невозможно корректно сформировать подпись.
    """
    signing_secret = _get_secret("SITE_ACCESS_COOKIE_PASSWORD")

    signature = hmac.new(
        signing_secret.encode("utf-8"),
        ACCESS_VERSION.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{ACCESS_VERSION}.{signature}"


def _sync_access_to_url() -> None:
    """
    Добавляет подтверждение бета-доступа в URL.

    Это важно для F5: после обновления Streamlit создаёт новую
    session_state, но URL сохраняется в браузере.
    """
    expected_token = _create_access_token()

    if _get_query_value(ACCESS_QUERY_PARAM) != expected_token:
        _set_query_value(
            ACCESS_QUERY_PARAM,
            expected_token,
        )


def _access_is_current() -> bool:
    """
    Проверяет доступ двумя способами:

    1. Внутри текущей Streamlit-сессии.
    2. По подписанному токену из URL — после F5 или нового запуска.
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


def _render_access_styles() -> None:
    """Подключает стили экрана закрытой бета-версии."""
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
                    #22D3EE 45%,
                    #8B5CF6 100%
                ) !important;
            color: #FFFFFF !important;
            font-size: 1rem;
            font-weight: 750;
            transition: transform 0.2s ease, filter 0.2s ease;
        }

        .stFormSubmitButton > button:hover {
            transform: translateY(-1px);
            filter: brightness(1.07);
        }

        .tm-access-note {
            margin-top: 1rem;
            color: #71829A;
            font-size: 0.82rem;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def require_site_access() -> None:
    """
    Проверяет пароль закрытой бета-версии.

    После первого успешного ввода:
    - доступ остаётся в session_state;
    - в URL записывается подписанное подтверждение;
    - после F5 доступ восстанавливается автоматически.
    """
    master_password = _get_secret("SITE_ACCESS_PASSWORD")

    if _access_is_current():
        # При переходе между страницами Streamlit может очищать
        # query-параметры. На каждой странице добавляем токен обратно.
        _sync_access_to_url()
        return

    _render_access_styles()

    st.markdown(
        """
        <div class="tm-access-card">
            <div class="tm-access-icon">✦</div>
            <h1 class="tm-access-title">TravelMind закрытая бета</h1>
            <p class="tm-access-text">
                Сервис находится в тестовом режиме. Введите код доступа,
                полученный от команды проекта.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 2.4, 1])

    with center:
        with st.form("site_access_form"):
            password = st.text_input(
                "Код доступа",
                type="password",
                placeholder="Введите мастер-пароль",
            )

            submitted = st.form_submit_button(
                "О
