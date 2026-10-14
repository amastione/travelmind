"""TravelMind — главная страница: вход и регистрация."""
import streamlit as st

import auth
import db

st.set_page_config(
    page_title="TravelMind — AI-планировщик путешествий",
    page_icon="🗺️",
    layout="centered",
    initial_sidebar_state="expanded",
)

db.init()

CSS = """
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
    color: #F4F7FB;
}

.block-container {
    max-width: 760px;
    padding-top: 4.2rem;
    padding-bottom: 4rem;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

h1, h2, h3 {
    color: #F8FAFC !important;
}

.tm-logo-wide {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1.35rem;
    width: fit-content;
    max-width: 100%;
    margin: 0 auto 1.2rem;
    padding: 1.05rem 1.55rem;
    border: 1px solid rgba(34, 211, 238, 0.28);
    border-radius: 22px;
    background: linear-gradient(
        135deg,
        rgba(10, 29, 53, 0.84),
        rgba(12, 22, 45, 0.72)
    );
    box-shadow:
        0 20px 55px rgba(0, 0, 0, 0.28),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.tm-map-symbol {
    position: relative;
    width: 105px;
    height: 84px;
    flex: 0 0 105px;
}

.tm-map-left,
.tm-map-center,
.tm-map-right {
    position: absolute;
    bottom: 5px;
    height: 43px;
    transform: skewY(18deg);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.20);
}

.tm-map-left {
    left: 4px;
    width: 34px;
    border-radius: 5px 0 0 5px;
    background: linear-gradient(145deg, #25CDED, #168DE6);
}

.tm-map-center {
    left: 37px;
    width: 34px;
    background: linear-gradient(145deg, #168EEA, #2778DA);
}

.tm-map-right {
    left: 70px;
    width: 32px;
    border-radius: 0 5px 5px 0;
    background: linear-gradient(145deg, #2586E2, #1B62BF);
}

.tm-map-fold-one,
.tm-map-fold-two {
    position: absolute;
    bottom: 5px;
    z-index: 2;
    width: 3px;
    height: 44px;
    background: rgba(7, 24, 49, 0.65);
    transform: skewY(18deg);
}

.tm-map-fold-one {
    left: 36px;
}

.tm-map-fold-two {
    left: 69px;
}

.tm-pin {
    position: absolute;
    z-index: 4;
    top: 0;
    left: 37px;
    width: 45px;
    height: 57px;
    border-radius: 50% 50% 50% 8px;
    background: linear-gradient(145deg, #27D7F1, #1975D5);
    transform: rotate(-45deg);
    box-shadow: 0 8px 18px rgba(34, 211, 238, 0.32);
}

.tm-pin::after {
    content: "";
    position: absolute;
    top: 13px;
    left: 13px;
    width: 19px;
    height: 19px;
    border-radius: 50%;
    background: #08172D;
}

.tm-logo-divider {
    width: 2px;
    height: 104px;
    background: linear-gradient(
        180deg,
        transparent 0%,
        rgba(255, 255, 255, 0.92) 14%,
        rgba(255, 255, 255, 0.92) 86%,
        transparent 100%
    );
}

.tm-logo-text {
    text-align: left;
    font-family: Arial, Helvetica, sans-serif;
    font-weight: 800;
    letter-spacing: 0.035em;
    line-height: 1.15;
}

.tm-logo-name {
    color: #F8FAFC;
    font-size: 1.5rem;
    white-space: nowrap;
}

.tm-logo-ai {
    color: #67E8F9;
}

.tm-logo-description {
    margin-top: 0.38rem;
    color: #D8E5F5;
    font-size: 0.82rem;
    line-height: 1.38;
    letter-spacing: 0.07em;
}

.tm-badge {
    margin: 0.4rem 0 1.7rem;
    text-align: center;
}

.tm-badge span {
    display: inline-block;
    padding: 0.4rem 0.9rem;
    border: 1px solid rgba(34, 211, 238, 0.30);
    border-radius: 999px;
    background: rgba(34, 211, 238, 0.08);
    color: #67E8F9;
    font-size: 0.84rem;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
    padding: 0.4rem;
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 16px;
    background: rgba(15, 23, 42, 0.55);
}

.stTabs [data-baseweb="tab"] {
    flex: 1;
    justify-content: center;
    height: 46px;
    border-radius: 11px;
    color: #AAB8CE;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(
        135deg,
        rgba(34, 211, 238, 0.20),
        rgba(139, 92, 246, 0.22)
    ) !important;
    color: #F8FAFC !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

[data-testid="stForm"] {
    margin-top: 1.25rem;
    padding: 1.7rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 22px;
    background: rgba(15, 23, 42, 0.72);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
}

[data-testid="stWidgetLabel"] p {
    color: #D6E0EF !important;
    font-weight: 600;
}

.stTextInput input {
    min-height: 48px;
    border: 1px solid rgba(148, 163, 184, 0.30) !important;
    border-radius: 12px !important;
    background: rgba(7, 11, 20, 0.65) !important;
    color: #F8FAFC !important;
}

.stTextInput input::placeholder {
    color: #72819A !important;
}

.stTextInput input:focus {
    border-color: #22D3EE !important;
    box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.15) !important;
}

.stButton > button,
.stFormSubmitButton > button {
    width: 100%;
    min-height: 48px;
    border: 0 !important;
    border-radius: 12px !important;
    background: linear-gradient(
        135deg,
        #06B6D4 0%,
        #22D3EE 45%,
        #8B5CF6 100%
    ) !important;
    color: #FFFFFF !important;
    font-size: 1rem;
    font-weight: 700;
    box-shadow: 0 10px 25px rgba(34, 211, 238, 0.18);
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-2px);
    filter: brightness(1.08);
}

.tm-welcome {
    padding: 1.75rem;
    border: 1px solid rgba(52, 211, 153, 0.30);
    border-radius: 22px;
    background: rgba(16, 38, 44, 0.55);
    text-align: center;
}

.tm-welcome-title {
    margin: 0;
    color: #F8FAFC;
    font-size: 1.5rem;
    font-weight: 750;
}

.tm-welcome-text {
    margin: 0.5rem 0 0;
    color: #B7C7DB;
}

[data-testid="stAlert"] {
    border-radius: 14px;
}

@media (max-width: 640px) {
    .block-container {
        padding-top: 2.4rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .tm-logo-wide {
        gap: 0.75rem;
        padding: 0.85rem 0.75rem;
    }

    .tm-map-symbol {
        transform: scale(0.72);
        margin-right: -21px;
    }

    .tm-logo-divider {
        height: 82px;
    }

    .tm-logo-name {
        font-size: 1.06rem;
    }

    .tm-logo-description {
        font-size: 0.64rem;
    }

    [data-testid="stForm"] {
        padding: 1.2rem;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

LOGO_HTML = """
<div class="tm-logo-wide" aria-label="TravelMind AI-планировщик путешествий">
    <div class="tm-map-symbol" aria-hidden="true">
        <div class="tm-map-left"></div>
        <div class="tm-map-center"></div>
        <div class="tm-map-right"></div>
        <div class="tm-map-fold-one"></div>
        <div class="tm-map-fold-two"></div>
        <div class="tm-pin"></div>
    </div>

    <div class="tm-logo-divider"></div>

    <div class="tm-logo-text">
        <div class="tm-logo-name">
            TRAVELMIND <span class="tm-logo-ai">AI</span>
        </div>
        <div class="tm-logo-description">
            ПЛАНИРОВАНИЕ<br>
            ПУТЕШЕСТВИЙ
        </div>
    </div>
</div>
"""

st.markdown(LOGO_HTML, unsafe_allow_html=True)

st.markdown(
    """
    <div class="tm-badge">
        <span>✦ AI Travel Planner · Учебный MVP</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if "user_id" in st.session_state:
    username = st.session_state.get("username", "путешественник")

    st.markdown(
        f"""
        <div class="tm-welcome">
            <p class="tm-welcome-title">Рады видеть вас, {username}! 👋</p>
            <p class="tm-welcome-text">
                Выберите действие и продолжите планировать путешествие.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    column_1, column_2 = st.columns(2)

    with column_1:
        st.page_link(
            "pages/1_new_trip.py",
            label="✈️ Спланировать поездку",
            use_container_width=True,
        )

    with column_2:
        st.page_link(
            "pages/2_my_trips.py",
            label="🧳 Мои путешествия",
            use_container_width=True,
        )

    st.write("")

    if st.button("Выйти из аккаунта"):
        auth.logout()
        st.rerun()

    st.stop()

tab_login, tab_register = st.tabs(
    [
        "🔐 Войти",
        "✨ Создать аккаунт",
    ]
)

with tab_login:
    st.markdown("#### С возвращением!")
    st.caption("Введите данные аккаунта, чтобы продолжить.")

    with st.form("login_form"):
        username = st.text_input(
            "Логин",
            placeholder="Введите логин",
        )

        password = st.text_input(
            "Пароль",
            type="password",
            placeholder="Введите пароль",
        )

        submitted = st.form_submit_button("Войти в TravelMind")

        if submitted:
            error = auth.login(username, password)

            if error:
                st.error(error)
            else:
                st.rerun()

with tab_register:
    st.markdown("#### Начните планировать путешествия")
    st.caption("Создание аккаунта займёт меньше минуты.")

    with st.form("register_form"):
        username = st.text_input(
            "Логин",
            key="register_username",
            placeholder="Придумайте логин",
        )

        password = st.text_input(
            "Пароль",
            type="password",
            key="register_password",
            placeholder="Придумайте пароль",
        )

        password_repeat = st.text_input(
            "Повторите пароль",
            type="password",
            key="register_password_repeat",
            placeholder="Введите пароль ещё раз",
        )

        submitted = st.form_submit_button("Создать аккаунт")

        if submitted:
            if password != password_repeat:
                st.error("Пароли не совпадают.")
            else:
                error = auth.register(username, password)

                if error:
                    st.error(error)
                else:
                    auth.login(username, password)
                    st.rerun()
