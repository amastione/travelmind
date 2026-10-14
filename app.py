"""TravelMind — главная страница: вход и регистрация."""
import streamlit as st

import auth
import db

st.set_page_config(
    page_title="TravelMind — AI-планировщик путешествий",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Инициализация базы данных
db.init()

# ---------- СТИЛИ ----------

st.markdown(
    """
    <style>
        /* Основной тёмный фон */
        .stApp {
            background:
                radial-gradient(
                    circle at 15% 10%,
                    rgba(34, 211, 238, 0.16) 0%,
                    transparent 30%
                ),
                radial-gradient(
                    circle at 90% 85%,
                    rgba(139, 92, 246, 0.18) 0%,
                    transparent 35%
                ),
                linear-gradient(
                    135deg,
                    #070B14 0%,
                    #0D1628 50%,
                    #101426 100%
                );
            color: #F4F7FB;
        }

        /* Основной контейнер */
        .block-container {
            max-width: 760px;
            padding-top: 4.5rem;
            padding-bottom: 4rem;
        }

        /* Скрываем технические элементы Streamlit */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        /* ---------- Брендовая зона ---------- */

        .tm-logo {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 80px;
            height: 80px;
            margin: 0 auto 1.2rem;
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 26px;
            background:
                radial-gradient(
                    circle at 28% 25%,
                    rgba(255, 255, 255, 0.38),
                    transparent 27%
                ),
                linear-gradient(
                    135deg,
                    #22D3EE 0%,
                    #4F8EF7 50%,
                    #8B5CF6 100%
                );
            color: #FFFFFF;
            font-size: 1.7rem;
            font-weight: 850;
            letter-spacing: -0.12rem;
            box-shadow:
                0 18px 42px rgba(34, 211, 238, 0.22),
                0 14px 32px rgba(139, 92, 246, 0.25);
        }

        /* Центрируем заголовок TravelMind */
        .tm-brand-title {
            text-align: center;
        }

        .tm-brand-title h1 {
            margin: 0 !important;
            color: #F8FAFC !important;
            font-size: 2.8rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.08rem !important;
        }

        /* Центрируем подзаголовок */
        .tm-brand-subtitle {
            margin-top: 0.75rem;
            text-align: center;
        }

        .tm-brand-subtitle p {
            margin: 0 !important;
            color: #AAB8CE !important;
            font-size: 1.08rem !important;
            line-height: 1.65 !important;
            text-align: center !important;
        }

        .tm-badge {
            margin-top: 1.15rem;
            text-align: center;
        }

        .tm-badge span {
            display: inline-block;
            padding: 0.38rem 0.85rem;
            border: 1px solid rgba(34, 211, 238, 0.30);
            border-radius: 999px;
            background: rgba(34, 211, 238, 0.08);
            color: #67E8F9;
            font-size: 0.84rem;
        }

        /* ---------- Вкладки входа и регистрации ---------- */

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

        /* ---------- Карточка формы ---------- */

        [data-testid="stForm"] {
            margin-top: 1.25rem;
            padding: 1.7rem;
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 22px;
            background: rgba(15, 23, 42, 0.72);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
            backdrop-filter: blur(16px);
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

        /* ---------- Кнопки ---------- */

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

        /* ---------- Блок пользователя после авторизации ---------- */

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

        /* Мобильная версия */
        @media (max-width: 640px) {
            .block-container {
                padding-top: 2.5rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .tm-brand-title h1 {
                font-size: 2.3rem !important;
            }

            .tm-brand-subtitle p {
                font-size: 1rem !important;
            }

            [data-testid="stForm"] {
                padding: 1.2rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- БРЕНД TRAVELMIND ----------
# Используются простые HTML-блоки, без SVG и сложной разметки.

st.markdown(
    '<div class="tm-logo">TM</div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="tm-brand-title">', unsafe_allow_html=True)
st.title("TravelMind")
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="tm-brand-subtitle">', unsafe_allow_html=True)
st.caption(
    "Персональные путешествия, спланированные "
    "искусственным интеллектом."
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="tm-badge">
        <span>✦ AI Travel Planner · Учебный MVP</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.write("")

# ---------- ПОЛЬЗОВАТЕЛЬ УЖЕ ВОШЁЛ ----------

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

# ---------- ВХОД И РЕГИСТРАЦИЯ ----------

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
