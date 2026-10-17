"""TravelMind — главная страница: вход и регистрация."""

import base64
from pathlib import Path

import streamlit as st

import auth
import branding
import db
import site_access


st.set_page_config(
    page_title="TravelMind — AI-планировщик путешествий",
    page_icon="🗺️",
    layout="centered",
    initial_sidebar_state="expanded",
)

branding.apply_clean_layout()
site_access.require_site_access()
db.init()

# Восстанавливает пользователя после обновления страницы.
auth.restore_session()


def get_logo_html():
    """
    Загружает PNG-логотип как data URL.
    Такой способ позволяет аккуратно стилизовать изображение через HTML/CSS.
    """
    logo_path = Path("assets/brand/travelmind_logo.png")

    if not logo_path.exists():
        return """
        <div class="tm-logo-fallback">
            TravelMind
        </div>
        """

    image_base64 = base64.b64encode(logo_path.read_bytes()).decode("utf-8")

    return f"""
    <div class="tm-brand-wrap">
        <div class="tm-brand-card">
            <img
                class="tm-brand-image"
                src="data:image/png;base64,{image_base64}"
                alt="TravelMind"
            >
        </div>
    </div>
    """


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
    padding-top: 3.2rem;
    padding-bottom: 4rem;
}

#MainMenu,
footer {
    visibility: hidden;
}

/*
 span намеренно не указан:
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
   PNG-ЛОГОТИП TRAVELMIND
   ---------------------------------------------------------- */

.tm-brand-wrap {
    display: flex;
    justify-content: center;
    width: 100%;
    margin: 0 auto;
}

.tm-brand-card {
    display: flex;
    align-items: center;
    justify-content: center;
    width: min(100%, 620px);
    min-height: 128px;
    padding: 1rem 1.5rem;
    border: 1px solid rgba(103, 232, 249, 0.23);
    border-radius: 26px;
    background:
        radial-gradient(
            circle at 15% 10%,
            rgba(34, 211, 238, 0.15),
            transparent 42%
        ),
        radial-gradient(
            circle at 90% 90%,
            rgba(139, 92, 246, 0.12),
            transparent 38%
        ),
        linear-gradient(
            135deg,
            rgba(16, 34, 57, 0.95),
            rgba(12, 20, 42, 0.96)
        );
    box-shadow:
        0 18px 42px rgba(0, 0, 0, 0.25),
        0 0 36px rgba(34, 211, 238, 0.08),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.tm-brand-image {
    display: block;
    width: min(100%, 520px);
    height: auto;
    max-height: 145px;
    object-fit: contain;
}

.tm-logo-fallback {
    margin: 0 auto;
    color: #F8FAFC;
    font-size: 2.6rem;
    font-weight: 850;
    letter-spacing: -0.08rem;
    text-align: center;
}

.tm-brand-subtitle {
    margin-top: 1.15rem;
    color: #67E8F9;
    font-size: 1rem;
    font-weight: 800;
    letter-spacing: 0.09rem;
    text-align: center;
}

.tm-brand-description {
    margin-top: 0.34rem;
    color: #AAB8CE;
    font-size: 0.83rem;
    font-weight: 550;
    letter-spacing: 0.055rem;
    text-align: center;
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
   ПЕРЕКЛЮЧАТЕЛЬ «ВХОД / РЕГИСТРАЦИЯ»
   ---------------------------------------------------------- */

.stTabs {
    margin-top: 0.4rem;
}

[data-testid="stTabs"] [data-baseweb="tab-list"],
.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    gap: 0.45rem !important;
    width: 100% !important;
    min-height: 64px !important;
    padding: 0.42rem !important;
    border: 1px solid rgba(103, 232, 249, 0.20) !important;
    border-radius: 18px !important;
    background:
        linear-gradient(
            135deg,
            rgba(19, 34, 56, 0.88),
            rgba(15, 21, 45, 0.86)
        ) !important;
    box-shadow:
        0 12px 28px rgba(0, 0, 0, 0.14),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

[data-testid="stTabs"] [data-baseweb="tab-border"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

[data-testid="stTabs"] button[role="tab"],
.stTabs button[role="tab"],
.stTabs [data-baseweb="tab"] {
    display: inline-flex !important;
    flex: 1 1 0 !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 52px !important;
    margin: 0 !important;
    padding: 0.75rem 1rem !important;
    border: 1px solid transparent !important;
    border-radius: 13px !important;
    background: transparent !important;
    color: #AFC1D7 !important;
    font-size: 1rem !important;
    font-weight: 750 !important;
    letter-spacing: -0.01rem !important;
    white-space: nowrap !important;
}

[data-testid="stTabs"] button[role="tab"] p,
.stTabs button[role="tab"] p,
.stTabs [data-baseweb="tab"] p {
    margin: 0 !important;
    color: inherit !important;
    font-size: 1rem !important;
    font-weight: 750 !important;
}

[data-testid="stTabs"] button[role="tab"]:hover,
.stTabs button[role="tab"]:hover,
.stTabs [data-baseweb="tab"]:hover {
    border-color: rgba(103, 232, 249, 0.28) !important;
    background: rgba(103, 232, 249, 0.08) !important;
    color: #DFFBFF !important;
}

[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
.stTabs button[role="tab"][aria-selected="true"],
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    border: 1px solid rgba(233, 253, 255, 0.70) !important;
    background:
        linear-gradient(
            135deg,
            #06B6D4 0%,
            #22D3EE 44%,
            #4D8CF2 74%,
            #8656E8 100%
        ) !important;
    color: #FFFFFF !important;
    box-shadow:
        0 8px 18px rgba(34, 211, 238, 0.21),
        0 5px 15px rgba(139, 92, 246, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.30) !important;
}

/* ----------------------------------------------------------
   ФОРМЫ
   ---------------------------------------------------------- */

[data-testid="stForm"] {
    margin-top: 1.25rem;
    padding: 1.7rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 22px;
    background:
        linear-gradient(
            135deg,
            rgba(17, 30, 53, 0.80),
            rgba(14, 22, 43, 0.78)
        );
    box-shadow:
        0 20px 60px rgba(0, 0, 0, 0.24),
        inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

[data-testid="stWidgetLabel"] p {
    color: #D6E0EF !important;
    font-weight: 650 !important;
}

.stTextInput input,
[data-testid="stTextInput"] input,
[data-baseweb="input"] input {
    min-height: 50px !important;
    border: 1px solid rgba(148, 163, 184, 0.36) !important;
    border-radius: 12px !important;
    background: rgba(7, 13, 26, 0.78) !important;
    color: #F8FAFC !important;
    font-size: 1rem !important;
}

.stTextInput input::placeholder,
[data-testid="stTextInput"] input::placeholder,
[data-baseweb="input"] input::placeholder {
    color: #71839F !important;
}

.stTextInput input:focus,
[data-testid="stTextInput"] input:focus,
[data-baseweb="input"] input:focus {
    border-color: #22D3EE !important;
    box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.15) !important;
}

[data-testid="stTextInput"] button {
    border-radius: 0 12px 12px 0 !important;
    background: rgba(16, 29, 50, 0.92) !important;
    color: #BDEFF7 !important;
}

/* ----------------------------------------------------------
   КНОПКИ
   ---------------------------------------------------------- */

.stButton > button,
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
        padding-top: 2rem;
        padding-right: 1rem;
        padding-left: 1rem;
    }

    .tm-brand-card {
        width: min(100%, 440px);
        min-height: 90px;
        padding: 0.7rem 0.9rem;
        border-radius: 19px;
    }

    .tm-brand-image {
        max-height: 100px;
    }

    .tm-brand-subtitle {
        margin-top: 0.9rem;
        font-size: 0.78rem;
        letter-spacing: 0.045rem;
    }

    .tm-brand-description {
        font-size: 0.65rem;
        letter-spacing: 0.025rem;
    }

    [data-testid="stForm"] {
        padding: 1.2rem;
    }

    [data-testid="stTabs"] [data-baseweb="tab-list"],
    .stTabs [data-baseweb="tab-list"] {
        min-height: 58px !important;
        border-radius: 15px !important;
    }

    [data-testid="stTabs"] button[role="tab"],
    .stTabs button[role="tab"],
    .stTabs [data-baseweb="tab"] {
        min-height: 46px !important;
        padding: 0.65rem 0.7rem !important;
        font-size: 0.92rem !important;
    }

    [data-testid="stTabs"] button[role="tab"] p,
    .stTabs button[role="tab"] p,
    .stTabs [data-baseweb="tab"] p {
        font-size: 0.92rem !important;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ==========================================================
# ЛОГОТИП
# ==========================================================

st.markdown(get_logo_html(), unsafe_allow_html=True)

st.markdown(
    """
    <div class="tm-brand-subtitle">AI-ПЛАНИРОВЩИК</div>

    <div class="tm-brand-description">
        ПЕРСОНАЛЬНЫХ ПУТЕШЕСТВИЙ
    </div>
    """,
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
        if st.button(
            "✈️ Спланировать поездку",
            key="go_to_new_trip",
            use_container_width=True,
        ):
            st.switch_page("pages/1_new_trip.py")

    with column_2:
        if st.button(
            "🧳 Мои путешествия",
            key="go_to_my_trips",
            use_container_width=True,
        ):
            st.switch_page("pages/2_my_trips.py")

    st.write("")

    if st.button(
        "Выйти из аккаунта",
        key="logout_button",
    ):
        auth.logout()
        site_access.revoke_site_access()
        st.rerun()

    st.stop()

# ==========================================================
# ВХОД И РЕГИСТРАЦИЯ
# ==========================================================

tab_login, tab_register = st.tabs(
    [
        "Вход",
        "Регистрация",
    ]
)

with tab_login:
    st.markdown("#### С возвращением")

    st.caption(
        "Войдите, чтобы открыть сохранённые маршруты, карту и бюджет поездок."
    )

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

        submitted = st.form_submit_button("Продолжить →")

        if submitted:
            error = auth.login(username, password)

            if error:
                st.error(error)
            else:
                st.rerun()

with tab_register:
    st.markdown("#### Создайте аккаунт")

    st.caption(
        "Сохраняйте маршруты, отслеживайте бюджет и возвращайтесь к планам."
    )

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

        submitted = st.form_submit_button("Создать аккаунт →")

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

st.markdown(
    """
    <div class="tm-author">
        Concept & design by <strong>Michael Degtyarev</strong>
    </div>
    """,
    unsafe_allow_html=True,
)
