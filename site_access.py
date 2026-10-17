"""Общий пароль для доступа к закрытой бета-версии TravelMind."""

import hmac

import streamlit as st


MASTER_PASSWORD = "TravelMind2026"

ACCESS_VERSION = "2026-10-18-v1"


def _access_is_current() -> bool:
    """Проверяет доступ в рамках текущей Streamlit-сессии."""
    return (
        st.session_state.get("site_access_granted") is True
        and st.session_state.get("site_access_version") == ACCESS_VERSION
    )


def require_site_access() -> None:
    """Показывает форму общего доступа, если пароль ещё не введён."""
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
            font-size: 3rem;
        }

        .tm-access-title {
            margin: 0.4rem 0;
            color: #F8FAFC;
            font-size: 2rem;
            font-weight: 800;
        }

        .tm-access-text {
            color: #B6C6DB;
            font-size: 1rem;
            line-height: 1.65;
        }

        .stTextInput input {
            min-height: 50px !important;
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

    st.markdown(
        """
        <div class="tm-access-card">
            <div class="tm-access-icon">✦</div>
            <div class="tm-access-title">TravelMind закрытая бета</div>
            <div class="tm-access-text">
                Сервис находится в тестовом режиме.
                Введите код доступа, полученный от команды проекта.
            </div>
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
                if hmac.compare_digest(
                    password.strip(),
                    MASTER_PASSWORD,
                ):
                    st.session_state["site_access_granted"] = True
                    st.session_state["site_access_version"] = ACCESS_VERSION
                    st.rerun()

                else:
                    st.error("Неверный код доступа. Попробуйте ещё раз.")

    st.stop()


def revoke_site_access() -> None:
    """Очищает доступ закрытой беты из текущей сессии."""
    st.session_state.pop("site_access_granted", None)
    st.session_state.pop("site_access_version", None)
