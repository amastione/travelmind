"""Общий пароль для доступа к закрытой бета-версии TravelMind."""

import hmac

import streamlit as st


# ==========================================================
# НАСТРОЙКИ ЗАКРЫТОГО ДОСТУПА
# ==========================================================
#
# ТЕКУЩИЙ ПАРОЛЬ:
# TravelMind2026
#
# Чтобы поменять пароль и забрать доступ у всех пользователей:
#
# 1. Измените MASTER_PASSWORD на новый пароль.
# 2. Измените ACCESS_VERSION, например v2 → v3.
# 3. Нажмите Commit changes в GitHub.
#
# После автоматического обновления Streamlit старый доступ
# перестанет работать, а пользователям понадобится новый пароль.
#
# ВАЖНО:
# Если GitHub-репозиторий публичный, пароль будет виден в коде.
# Для учебного проекта это допустимо. Для публичного релиза
# пароль следует хранить в Streamlit Secrets.
# ==========================================================

MASTER_PASSWORD = "TravelMind2026"

ACCESS_VERSION = "2026-10-14-v2"


def _access_is_current() -> bool:
    """
    Проверяет, прошёл ли пользователь общий пароль
    именно для текущей версии доступа.
    """
    return (
        st.session_state.get("site_access_granted") is True
        and st.session_state.get("site_access_version") == ACCESS_VERSION
    )


def require_site_access() -> None:
    """
    Проверяет доступ к закрытой версии TravelMind.

    Если пользователь ещё не ввёл верный мастер-пароль,
    отображается экран закрытой бета-версии и работа страницы
    останавливается через st.stop().
    """
    if _access_is_current():
        return

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
                    MASTER_PASSWORD,
                ):
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

    # Не позволяет открыть содержимое остальных страниц,
    # пока пользователь не введёт корректный общий пароль.
    st.stop()


def revoke_site_access() -> None:
    """
    Удаляет доступ к закрытой бета-версии в текущем браузере.
    Используется при полном выходе из сервиса.
    """
    st.session_state.pop("site_access_granted", None)
    st.session_state.pop("site_access_version", None)
