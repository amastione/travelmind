"""Общий пароль для закрытого тестового доступа к TravelMind."""
import hashlib
import hmac

import streamlit as st


# ==========================================================
# НАСТРОЙКИ ДОСТУПА
# ==========================================================
#
# 1. MASTER_PASSWORD_HASH — SHA-256 хеш мастер-пароля.
# 2. ACCESS_VERSION — версия доступа.
#
# Чтобы отозвать доступ у всех тестировщиков:
# - смените пароль;
# - обновите хеш;
# - измените ACCESS_VERSION;
# - сделайте Commit changes в GitHub.
#
# Пример:
# ACCESS_VERSION = "2026-10-14-v2"
# ==========================================================

MASTER_PASSWORD_HASH = (
    "TravelMind2026"
)

ACCESS_VERSION = "2026-10-14-v2"


def _hash_password(password: str) -> str:
    """Возвращает SHA-256 хеш пароля."""
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def _access_is_current() -> bool:
    """
    Проверяет, что доступ был подтверждён для текущей версии доступа.
    Если ACCESS_VERSION изменится после деплоя, старый доступ станет
    недействительным при следующем перезапуске Streamlit.
    """
    return (
        st.session_state.get("site_access_granted") is True
        and st.session_state.get("site_access_version") == ACCESS_VERSION
    )


def require_site_access() -> None:
    """
    Показывает страницу ввода общего пароля, если доступ не подтверждён.
    После успешного ввода выполнение текущей страницы продолжается.
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
            margin: 5vh auto 1.1rem;
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
            margin: 0.7rem auto 0;
            max-width: 470px;
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
                    #06B6D4 0%,
                    #22D3EE 45%,
                    #8B5CF6 100%
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
                if hmac.compare_digest(
                    password.strip(),
                    MASTER_PASSWORD,
                ):
                    st.session_state["site_access_granted"] = True
                    st.session_state["site_access_version"] = ACCESS_VERSION
                    st.rerun()

                st.error("Неверный код доступа.")

    st.stop()


def revoke_site_access() -> None:
    """Очищает доступ к закрытой бета-версии в текущем браузере."""
    st.session_state.pop("site_access_granted", None)
    st.session_state.pop("site_access_version", None)
