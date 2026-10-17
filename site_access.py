"""Общий пароль для доступа к закрытой бета-версии TravelMind."""

import hashlib
import hmac

import streamlit as st


# ==========================================================
# НАСТРОЙКИ
# ==========================================================

# При изменении версии всем пользователям потребуется снова
# ввести общий пароль бета-доступа.
ACCESS_VERSION = "2026-10-18-v4"

# Имя служебного параметра в адресной строке.
# Он не содержит сам пароль.
ACCESS_QUERY_PARAM = "tm_beta"


def _get_secret(name: str) -> str:
    """Получает обязательное значение из Streamlit Secrets."""
    try:
        return str(st.secrets[name])
    except KeyError:
        st.error(
            f"В Streamlit Secrets не найден параметр: {name}"
        )
        st.stop()


def _get_query_value(name: str) -> str:
    """Безопасно читает одиночный query-параметр."""
    value = st.query_params.get(name, "")

    if isinstance(value, list):
        return str(value[0]) if value else ""

    return str(value or "")


def _set_query_value(name: str, value: str) -> None:
    """Добавляет или обновляет один query-параметр."""
    st.query_params[name] = str(value)


def _remove_query_value(name: str) -> None:
    """Удаляет query-параметр, если он существует."""
    try:
        del st.query_params[name]
    except KeyError:
        pass


def _create_access_token() -> str:
    """
    Создаёт криптографически подписанный маркер доступа.

    Формат:
    ACCESS_VERSION.HMAC_SIGNATURE

    В URL не передаётся ни мастер-пароль, ни секрет из Secrets.
    """
    signing_secret = _get_secret("SITE_ACCESS_COOKIE_PASSWORD")

    signature = hmac.new(
        signing_secret.encode("utf-8"),
        ACCESS_VERSION.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{ACCESS_VERSION}.{signature}"


def _restore_access_from_url() -> bool:
    """
    Проверяет подписанный токен в URL и восстанавливает доступ
    в новой Streamlit-сессии после F5.
    """
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
    Добавляет tm_beta в URL.

    Другие параметры не удаляются:
    - tm_auth — авторизация пользователя;
    - tm_trip — открытая поездка.
    """
    token = _create_access_token()

    if _get_query_value(ACCESS_QUERY_PARAM) != token:
        _set_query_value(ACCESS_QUERY_PARAM, token)


def _access_is_current() -> bool:
    """Проверяет текущую сессию либо восстанавливает доступ из URL."""
    in_current_session = (
        st.session_state.get("site_access_granted") is True
        and st.session_state.get("site_access_version")
        == ACCESS_VERSION
    )

    if in_current_session:
        return True

    return _restore_access_from_url()


def _render_access_styles() -> None:
    """Стили страницы закрытой беты."""
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
            box-shadow:
                0 20px 60px rgba(0, 0, 0, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }

        .tm-access-card {
            max-width: 560px;
            margin: 7vh auto 1.2rem;
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

        .stFormSubmitButton > button {
            width: 100%;
            min-height: 50px;
            border: 0 !important;
            border-radius: 13px !important;
            background:
                linear-gradient(
                    135deg,
                    #06B6D4,
                    #22D3EE,
                    #8B5CF6
                ) !important;
            color: #FFFFFF !important;
            font-size: 1rem;
            font-weight: 750;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def require_site_access() -> None:
    """
    Проверяет доступ к закрытой бета-версии.

    После успешного ввода пароль не сохраняется в браузере.
    Вместо него в URL записывается подписанный служебный токен.
    Он переживает F5 и позволяет восстановить доступ.
    """
    master_password = _get_secret("SITE_ACCESS_PASSWORD")

    if _access_is_current():
        # При переходе между страницами Streamlit иногда меняет URL.
        # Возвращаем только параметр tm_beta, не трогая tm_auth/tm_trip.
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
                "Открыть TravelMind"
            )

            if submitted:
                entered_password = password.strip()

                if hmac.compare_digest(
                    entered_password,
                    master_password,
                ):
                    st.session_state["site_access_granted"] = True
                    st.session_state["site_access_version"] = ACCESS_VERSION

                    # Добавляет служебный токен в URL до rerun.
                    _sync_access_to_url()
                    st.rerun()

                else:
                    st.error("Неверный код доступа. Попробуйте ещё раз.")

    st.stop()


def revoke_site_access() -> None:
    """Удаляет доступ закрытой беты из URL и текущей сессии."""
    _remove_query_value(ACCESS_QUERY_PARAM)

    st.session_state.pop("site_access_granted", None)
    st.session_state.pop("site_access_version", None)
