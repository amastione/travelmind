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

# Восстанавливает пользователя после обновления страницы.
auth.restore_session()

CSS = """
<style>
/* ----------------------------------------------------------
   ОСНОВА
   ---------------------------------------------------------- */

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
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;
}

.block-container {
    max-width: 850px;
    padding-top: 3.5rem;
    padding-bottom: 4rem;
}

#MainMenu,
footer {
    visibility: hidden;
}

/*
 Важно: span намеренно не указан.
 Streamlit использует span для Material Icons.
*/
h1,
h2,
h3,
h4,
p,
label,
button,
[data-testid="stMarkdownContainer"] {
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif !important;
}

.material-symbols-rounded,
.material-symbols-outlined,
.material-icons,
[data-testid="stIconMaterial"] {
    font-family:
        "Material Symbols Rounded",
        "Material Symbols Outlined",
        "Material Icons" !important;
    font-style: normal !important;
}

h1,
h2,
h3 {
    color: #F8FAFC !important;
}

/* ----------------------------------------------------------
   ЛОГОТИП
   ---------------------------------------------------------- */

.tm-map-symbol {
    position: relative;
    width: 125px;
    height: 100px;
    margin: 0 auto;
}

.tm-map-left,
.tm-map-center,
.tm-map-right {
    position: absolute;
    bottom: 7px;
    height: 50px;
    transform: skewY(18deg);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.20);
}

.tm-map-left {
    left: 4px;
    width: 41px;
    border-radius: 6px 0 0 6px;
    background: linear-gradient(145deg, #25CDED, #168DE6);
}

.tm-map-center {
    left: 44px;
    width: 41px;
    background: linear-gradient(145deg, #168EEA, #2778DA);
}

.tm-map-right {
    left: 84px;
    width: 37px;
    border-radius: 0 6px 6px 0;
    background: linear-gradient(145deg, #2586E2, #1B62BF);
}

.tm-map-fold-one,
.tm-map-fold-two {
    position: absolute;
    bottom: 7px;
    z-index: 2;
    width: 3px;
    height: 51px;
    background: rgba(7, 24, 49, 0.65);
    transform: skewY(18deg);
}

.tm-map-fold-one {
    left: 43px;
}

.tm-map-fold-two {
    left: 83px;
}

.tm-pin {
    position: absolute;
    z-index: 4;
    top: 0;
    left: 43px;
    width: 52px;
    height: 65px;
    border-radius: 50% 50% 50% 9px;
    background: linear-gradient(145deg, #27D7F1, #1975D5);
    transform: rotate(-45deg);
    box-shadow: 0 9px 20px rgba(34, 211, 238, 0.32);
}

.tm-pin::after {
    content: "";
    position: absolute;
    top: 15px;
    left: 15px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #08172D;
}

.tm-divider {
    width: 2px;
    height: 118px;
    margin: 0 auto;
    background: linear-gradient(
        180deg,
        transparent 0%,
        rgba(255, 255, 255, 0.95) 14%,
        rgba(255, 255, 255, 0.95) 86%,
        transparent 100%
    );
}

.tm-logo-title h1 {
    margin: 0 !important;
    padding: 0 !important;
    color: #F8FAFC !important;
    font-size: 2.55rem !important;
    font-weight: 850 !important;
    letter-spacing: -0.08rem !important;
    line-height: 1.05 !important;
}

.tm-logo-subtitle {
    margin-top: 0.35rem;
    color: #67E8F9;
    font-size: 1rem;
    font-weight: 750;
    letter-spacing: 0.08rem;
}

.tm-logo-description {
    margin-top: 0.3rem;
    color: #AAB8CE;
    font-size: 0.83rem;
    font-weight: 500;
    letter-spacing: 0.055rem;
}

.tm-badge {
    margin: 1rem 0 1.7rem;
    text-align: center;
}

.tm-badge span {
    display: inline-block;
    padding: 0.42rem 0.95rem;
    border: 1px solid rgba(34, 211, 238, 0.30);
    border-radius: 999px;
    background: rgba(34, 211, 238, 0.08);
    color: #67E8F9;
    font-size: 0.84rem;
}

/* ----------------------------------------------------------
   ВКЛАДКИ АВТОРИЗАЦИИ
   ---------------------------------------------------------- */

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

/* ----------------------------------------------------------
   ФОРМЫ
   ---------------------------------------------------------- */

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

/* ----------------------------------------------------------
   СТАНДАРТНЫЕ КНОПКИ И ФОРМЫ
   ---------------------------------------------------------- */

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
    transition:
        transform 180ms ease,
        filter 180ms ease,
        box-shadow 180ms ease;
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    transform: translateY(-2px);
    filter: brightness(1.08);
    box-shadow: 0 15px 30px rgba(34, 211, 238, 0.26);
}

/* ----------------------------------------------------------
   ПРИВЕТСТВЕННЫЙ БЛОК
   ---------------------------------------------------------- */

.tm-welcome {
    padding: 1.75rem;
    border: 1px solid rgba(52, 211, 153, 0.30);
    border-radius: 22px;
    background:
        linear-gradient(
            135deg,
            rgba(16, 49, 57, 0.62),
            rgba(22, 33, 61, 0.60)
        );
    box-shadow:
        0 16px 38px rgba(0, 0, 0, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.05);
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

/* ----------------------------------------------------------
   ОСНОВНЫЕ CTA-КНОПКИ ГЛАВНОЙ СТРАНИЦЫ
   ---------------------------------------------------------- */

/* Общая структура ссылок на страницы */
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 72px !important;
    padding: 1rem 1.2rem !important;
    border-radius: 19px !important;
    text-decoration: none !important;
    font-size: 1.1rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.015rem !important;
    line-height: 1.2 !important;
    transition:
        transform 190ms ease,
        filter 190ms ease,
        border-color 190ms ease,
        box-shadow 190ms ease !important;
}

/* Текст и иконки внутри ссылок */
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] p,
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] span {
    color: #FFFFFF !important;
    font-size: 1.1rem !important;
    font-weight: 800 !important;
}

/*
 Основная кнопка: Спланировать поездку.
 href содержит имя файла страницы 1_new_trip.
*/
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"][href*="1_new_trip"] {
    border: 1px solid rgba(236, 254, 255, 0.62) !important;
    background:
        radial-gradient(
            circle at 25% 0%,
            rgba(255, 255, 255, 0.28),
            transparent 38%
        ),
        linear-gradient(
            135deg,
            #05B8D5 0%,
            #22D3EE 43%,
            #4E8DF2 73%,
            #8257E7 100%
        ) !important;
    box-shadow:
        0 14px 28px rgba(34, 211, 238, 0.23),
        0 8px 24px rgba(139, 92, 246, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.34) !important;
}

/*
 Вторичная кнопка: Мои путешествия.
 Хорошо заметна, но визуально слабее основной CTA.
*/
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"][href*="2_my_trips"] {
    border: 1px solid rgba(103, 232, 249, 0.46) !important;
    background:
        linear-gradient(
            135deg,
            rgba(20, 48, 71, 0.94),
            rgba(30, 37, 78, 0.92)
        ) !important;
    box-shadow:
        0 12px 26px rgba(0, 0, 0, 0.17),
        inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
}

/* Hover: основное действие */
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"][href*="1_new_trip"]:hover {
    transform: translateY(-3px) !important;
    filter: brightness(1.08) saturate(1.07) !important;
    box-shadow:
        0 20px 35px rgba(34, 211, 238, 0.29),
        0 12px 27px rgba(139, 92, 246, 0.22),
        inset 0 1px 0 rgba(255, 255, 255, 0.40) !important;
}

/* Hover: вторичное действие */
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"][href*="2_my_trips"]:hover {
    transform: translateY(-3px) !important;
    border-color: rgba(167, 139, 250, 0.82) !important;
    background:
        linear-gradient(
            135deg,
            rgba(27, 73, 96, 0.98),
            rgba(57, 43, 106, 0.98)
        ) !important;
    box-shadow:
        0 18px 33px rgba(34, 211, 238, 0.13),
        0 12px 26px rgba(139, 92, 246, 0.17),
        inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
}

/* Доступность: фокус клавиатурой */
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:focus-visible {
    outline: 3px solid rgba(103, 232, 249, 0.78) !important;
    outline-offset: 3px !important;
}

/* ----------------------------------------------------------
   СООБЩЕНИЯ
   ---------------------------------------------------------- */

[data-testid="stAlert"] {
    border-radius: 14px;
}

/* ----------------------------------------------------------
   МОБИЛЬНАЯ ВЕРСИЯ
   ---------------------------------------------------------- */

@media (max-width: 640px) {
    .block-container {
        padding-top: 2.3rem;
        padding-right: 1rem;
        padding-left: 1rem;
    }

    .tm-map-symbol {
        transform: scale(0.75);
        margin-left: -15px;
    }

    .tm-divider {
        height: 88px;
    }

    .tm-logo-title h1 {
        font-size: 1.75rem !important;
    }

    .tm-logo-subtitle {
        font-size: 0.74rem;
        letter-spacing: 0.04rem;
    }

    .tm-logo-description {
        font-size: 0.62rem;
        letter-spacing: 0.025rem;
    }

    [data-testid="stForm"] {
        padding: 1.2rem;
    }

    section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] {
        min-height: 64px !important;
        padding: 0.85rem 0.9rem !important;
        font-size: 0.98rem !important;
    }

    section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] p,
    section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] span {
        font-size: 0.98rem !important;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ==========================================================
# ЛОГОТИП
# ==========================================================

logo_map, logo_divider, logo_text = st.columns(
    [1.1, 0.1, 2.3],
    vertical_alignment="center",
)

with logo_map:
    st.markdown(
        """
        <div class="tm-map-symbol" aria-label="Карта и геометка">
            <div class="tm-map-left"></div>
            <div class="tm-map-center"></div>
            <div class="tm-map-right"></div>
            <div class="tm-map-fold-one"></div>
            <div class="tm-map-fold-two"></div>
            <div class="tm-pin"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with logo_divider:
    st.markdown(
        '<div class="tm-divider"></div>',
        unsafe_allow_html=True,
    )

with logo_text:
    st.markdown('<div class="tm-logo-title">', unsafe_allow_html=True)
    st.title("TravelMind")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        '<div class="tm-logo-subtitle">AI-ПЛАНИРОВЩИК</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="tm-logo-description">'
            'ПЕРСОНАЛЬНЫХ ПУТЕШЕСТВИЙ'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="tm-badge">
        <span>✦ AI Travel Planner · Учебный MVP</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# ПОЛЬЗОВАТЕЛЬ УЖЕ ВОШЁЛ
# ==========================================================

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

    column_1, column_2 = st.columns(2, gap="medium")

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

# ==========================================================
# ВХОД И РЕГИСТРАЦИЯ
# ==========================================================

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
