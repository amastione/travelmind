"""TravelMind — главная страница: вход и регистрация."""
import streamlit as st

import auth
import db

st.set_page_config(
    page_title="TravelMind — AI-планировщик путешествий",
    page_icon="🧭",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Инициализация базы
db.init()

# ---------- СТИЛИ ГЛАВНОЙ СТРАНИЦЫ ----------

st.markdown(
    """
    <style>
        /* Общий фон */
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
                linear-gradient(135deg, #070B14 0%, #0D1628 50%, #101426 100%);
            color: #F4F7FB;
        }

        /* Ограничиваем и центрируем основной контент */
        .block-container {
            max-width: 760px;
            padding-top: 4.5rem;
            padding-bottom: 4rem;
        }

        /* Убираем стандартные элементы Streamlit */
        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        /* Заголовки */
        h1, h2, h3 {
            color: #F8FAFC !important;
        }

        /* Верхняя бренд-зона */
        .tm-brand {
            text-align: center;
            margin-bottom: 2rem;
        }

        .tm-logo {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 72px;
            height: 72px;
            margin-bottom: 1rem;
            border-radius: 24px;
            font-size: 35px;
            background: linear-gradient(
                135deg,
                rgba(34, 211, 238, 0.95),
                rgba(139, 92, 246, 0.95)
            );
            box-shadow:
                0 12px 36px rgba(34, 211, 238, 0.20),
                0 12px 36px rgba(139, 92, 246, 0.20);
        }

        .tm-title {
            margin: 0;
            color: #F8FAFC;
            font-size: 2.7rem;
            font-weight: 800;
            line-height: 1.1;
            letter-spacing: -0.06rem;
        }

        .tm-subtitle {
            margin: 0.7rem auto 0;
            max-width: 480px;
            color: #AAB8CE;
            font-size: 1.08rem;
            line-height: 1.6;
        }

        .tm-badge {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.35rem 0.8rem;
            border: 1px solid rgba(34, 211, 238, 0.28);
            border-radius: 999px;
            background: rgba(34, 211, 238, 0.08);
            color: #67E8F9;
            font-size: 0.82rem;
        }

        /* Вкладки авторизации */
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

        /* Карточка формы */
        [data-testid="stForm"] {
            margin-top: 1.25rem;
            padding: 1.7rem;
            border: 1px solid rgba(148, 163, 184, 0.20);
            border-radius: 22px;
            background: rgba(15, 23, 42, 0.72);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.24);
            backdrop-filter: blur(16px);
        }

        /* Подписи и поля */
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

        .stTextInput input:focus {
            border-color: #22D3EE !important;
            box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.15) !important;
        }

        /* Основные кнопки */
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
            transition: transform 0.18s ease, filter 0.18s ease;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            transform: translateY(-2px);
            filter: brightness(1.08);
        }

        /* Информационные сообщения */
        [data-testid="stAlert"] {
            border-radius: 14px;
        }

        /* Карточки после входа */
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

        /* Адаптация под телефон */
        @media (max-width: 640px) {
            .block-container {
                padding-top: 2.5rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .tm-title {
                font-size: 2.2rem;
            }

            [data-testid="stForm"] {
                padding: 1.2rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- БРЕНД-ЗОНА ----------

st.markdown(
    """
    <div class="tm-brand">
        <div class="tm-logo">🧭</div>
        <h1 class="tm-title">TravelMind</h1>
        <p class="tm-subtitle">
            Персональные путешествия, спланированные
            искусственным интеллектом.
        </p>
        <span class="tm-badge">✦ AI Travel Planner · Учебный MVP</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- ЕСЛИ ПОЛЬЗОВАТЕЛЬ УЖЕ ВОШЁЛ ----------

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

    c1, c2 = st.columns(2)

    with c1:
        st.page_link(
            "pages/1_new_trip.py",
            label="✈️ Спланировать поездку",
            use_container_width=True,
        )

    with c2:
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

# ---------- АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ ----------

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
