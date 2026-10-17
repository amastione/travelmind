"""Общий пароль для доступа к закрытой бета-версии TravelMind."""

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

import extra_streamlit_components as stx
import streamlit as st


# ==========================================================
# НАСТРОЙКИ ЗАКРЫТОГО ДОСТУПА
# ==========================================================
#
# Обязательные параметры в Streamlit Secrets:
#
# SITE_ACCESS_PASSWORD = "пароль_закрытой_беты"
# SITE_ACCESS_COOKIE_PASSWORD = "длинный_случайный_секрет"
#
# SITE_ACCESS_COOKIE_PASSWORD — это технический секрет для
# криптографической подписи cookie. Пользователь его не вводит.
#
# Чтобы отозвать доступ у всех бета-тестеров:
# 1. Измените ACCESS_VERSION.
# 2. Сделайте Commit changes в GitHub.
#
# После обновления пользователям снова потребуется ввести
# пароль закрытой беты.
# ==========================================================

ACCESS_VERSION = "2026-10-17-v6"

COOKIE_NAME = "travelmind_beta_access"
COOKIE_DAYS = 30

# Ключ Streamlit-компонента CookieManager.
# Он должен быть постоянным, но менеджер должен создаваться
# только ОДИН раз за запуск страницы.
COOKIE_MANAGER_KEY = "travelmind_beta_cookie_manager"


def _get_secret(name: str) -> str:
    """Безопасно получает обязательное значение из Streamlit Secrets."""
    try:
        return str(st.secrets[name])
    except KeyError:
        st.error(
            f"В Streamlit Secrets отсутствует параметр: `{name}`. "
            "Проверьте настройки приложения."
        )
        st.stop()


def _get_cookie_manager():
    """
    Создаёт менеджер browser-cookie.

    Важно: CookieManager является Streamlit-компонентом, поэтому
    его нельзя создавать внутри @st.cache_resource / @st.cache_data.
    """
    return stx.CookieManager(
        key=COOKIE_MANAGER_KEY,
    )


def _create_access_token() -> str:
    """
    Создаёт подписанный токен для cookie.

    В cookie сохраняется не пароль закрытой беты, а строка вида:
    ACCESS_VERSION.HMAC_SHA256_SIGNATURE

    Подделать корректную подпись без SITE_ACCESS_COOKIE_PASSWORD нельзя.
    """
    signing_secret = _get_secret("SITE_ACCESS_COOKIE_PASSWORD")

    signature = hmac.new(
        signing_secret.encode("utf-8"),
        ACCESS_VERSION.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return f"{ACCESS_VERSION}.{signature}"


def _access_is_current(manager) -> bool:
    """
    Проверяет cookie с подтверждением доступа.

    При успешной проверке также восстанавливает доступ
    в текущем st.session_state.
    """
    saved_token = manager.get(COOKIE_NAME)
    expected_token = _create_access_token()

    if (
        saved_token
        and hmac.compare_digest(
            str(saved_token),
            expected_token,
        )
    ):
        st.session_state["site_access_granted"] = True
        st.session_state["site_access_version"] = ACCESS_VERSION
        return True

    return False


def _save_access_cookie(manager) -> None:
    """
    Сохраняет отметку о бета-доступе в браузере на COOKIE_DAYS дней.
    """
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=COOKIE_DAYS
    )

    manager.set(
        COOKIE_NAME,
        _create_access_token(),
        expires_at=expires_at,
    )


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
    Проверяет доступ к закрытой бета-версии TravelMind.

    Логика:
    1. Если доступ есть в текущем session_state — продолжаем работу.
    2. Если страницу обновили — восстанавливаем доступ из cookie.
    3. Если доступа нет — показываем форму с общим паролем.
    """
    master_password = _get_secret("SITE_ACCESS_PASSWORD")

    # Создаём компонент РОВНО ОДИН РАЗ за текущий запуск страницы.
    # Это устраняет StreamlitDuplicateElementKey.
    manager = _get_cookie_manager()

    # Быстрая проверка текущей сессии Streamlit.
    if (
        st.session_state.get("site_access_granted") is True
        and st.session_state.get("site_access_version")
        == ACCESS_VERSION
    ):
        return

    # Восстановление доступа после F5, закрытия/повторного открытия
    # вкладки и нового запуска Streamlit-сессии.
    if _access_is_current(manager):
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
                "Открыть TravelMind →"
            )

            if submitted:
                entered_password = password.strip()

                if hmac.compare_digest(
                    entered_password,
                    master_password,
                ):
                    # Сначала сохраняем cookie, затем обновляем session_state.
                    _save_access_cookie(manager)

                    st.session_state["site_access_granted"] = True
                    st.session_state["site_access_version"] = ACCESS_VERSION

                    st.rerun()

                else:
                    st.error("Неверный код доступа. Попробуйте ещё раз.")

        st.markdown(
            """
            <div class="tm-access-note">
                Доступ предоставляется только участникам тестирования.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()


def revoke_site_access() -> None:
    """
    Очищает только текущий session_state бета-доступа.

    Cookie специально не удаляется. Это сделано для удобства:
    после обычного выхода из аккаунта пользователь остаётся допущен
    к закрытой бете и может войти в другой аккаунт без повторного
    ввода общего пароля.

    Чтобы принудительно отозвать доступ у всех, измените ACCESS_VERSION.
    """
    st.session_state.pop("site_access_granted", None)
    st.session_state.pop("site_access_version", None)
