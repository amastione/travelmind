"""Общий пароль для доступа к закрытой бета-версии TravelMind."""

import hmac

import streamlit as st
from streamlit_cookies_manager import EncryptedCookieManager


# ==========================================================
# НАСТРОЙКИ ЗАКРЫТОГО ДОСТУПА
# ==========================================================
#
# Пароль и секрет cookie хранятся в Streamlit Secrets:
#
# SITE_ACCESS_PASSWORD = "пароль_для_бета-теста"
# SITE_ACCESS_COOKIE_PASSWORD = "длинная_случайная_секретная_строка"
#
# Чтобы забрать доступ у всех пользователей:
#
# 1. Измените ACCESS_VERSION.
# 2. Нажмите Commit changes в GitHub.
#
# После нового развёртывания старые cookie будут считаться
# неактуальными, и пользователи снова увидят форму доступа.
# ==========================================================

ACCESS_VERSION = "2026-10-17-v3"

COOKIE_NAME = "site_access"


def _get_cookie_manager() -> EncryptedCookieManager:
    """
    Создаёт менеджер зашифрованных cookie.

    Cookie сохраняется в браузере пользователя, поэтому доступ
    к закрытой бета-версии не пропадает после F5 / перезагрузки.
    """
    return EncryptedCookieManager(
        prefix="travelmind/",
        password=st.secrets["SITE_ACCESS_COOKIE_PASSWORD"],
    )


def _access_is_current(cookies: EncryptedCookieManager) -> bool:
    """
    Проверяет, есть ли в браузере действующая cookie доступа
    для текущей версии закрытой беты.
    """
    return cookies.get(COOKIE_NAME) == ACCESS_VERSION


def _render_access_page() -> None:
    """Отрисовывает интерфейс закрытого доступа."""
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


def require_site_access() -> None:
    """
    Проверяет доступ к закрытой бета-версии TravelMind.

    При первом визите пользователь вводит общий пароль. После успешного
    ввода в браузере сохраняется зашифрованная cookie. Поэтому при F5
    и обычной перезагрузке страницы пароль повторно не запрашивается.
    """
    try:
        master_password = st.secrets["SITE_ACCESS_PASSWORD"]
        cookies = _get_cookie_manager()

    except KeyError:
        st.error(
            "Не настроены Secrets для закрытого доступа. "
            "Добавьте SITE_ACCESS_PASSWORD и "
            "SITE_ACCESS_COOKIE_PASSWORD в Streamlit Secrets."
        )
        st.stop()

    # Cookie-компонент может быть не готов на первом запуске страницы.
    # После автоматического rerun Streamlit продолжит работу.
    if not cookies.ready():
        st.info("Проверяем доступ к TravelMind…")
        st.stop()

    # Допуск уже есть в постоянной cookie.
    if _access_is_current(cookies):
        st.session_state["site_access_granted"] = True
        st.session_state["site_access_version"] = ACCESS_VERSION
        return

    _render_access_page()

    left, center, right = st.columns([1, 2.4, 1])

    with center:
        with st.form("site_access_form"):
            password = st.text_input(
                "Код доступа",
                type="password",
                placeholder="Введите мастер-пароль",
            )

            submitted = st.form_submit_button("Открыть TravelMind →")

            if submitted:
                entered_password = password.strip()

                if hmac.compare_digest(
                    entered_password,
                    master_password,
                ):
                    # Сохраняем только факт прохождения доступа и версию.
                    # Сам мастер-пароль в cookie не записывается.
                    cookies[COOKIE_NAME] = ACCESS_VERSION
                    cookies.save()

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
    Отзывает доступ к закрытой бета-версии в текущем браузере.

    Вызывается при полном выходе пользователя из TravelMind.
    """
    try:
        cookies = _get_cookie_manager()

        if cookies.ready():
            cookies[COOKIE_NAME] = ""
            cookies.save()

    except KeyError:
        # Если Secrets ещё не настроены, просто очищаем session_state.
        pass

    st.session_state.pop("site_access_granted", None)
    st.session_state.pop("site_access_version", None)
