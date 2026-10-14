"""Страница создания поездки: форма параметров → LLM → запись в БД."""
import json
from datetime import date, timedelta

import streamlit as st

import ai
import auth
import db


st.set_page_config(
    page_title="Спланировать поездку",
    page_icon="✈️",
    layout="wide",
)

# Защита страницы: без входа сюда не пустим.
user_id = auth.require_auth()

CSS = """
<style>
.stApp {
    background:
        radial-gradient(
            circle at 10% 8%,
            rgba(34, 211, 238, 0.13),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 90%,
            rgba(139, 92, 246, 0.17),
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

.block-container {
    max-width: 1180px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

#MainMenu,
footer {
    visibility: hidden;
}

h1,
h2,
h3 {
    color: #F8FAFC !important;
}

.tm-page-eyebrow {
    color: #67E8F9;
    font-size: 0.82rem;
    font-weight: 750;
    letter-spacing: 0.09rem;
    text-transform: uppercase;
}

.tm-page-title {
    margin: 0.35rem 0 0 !important;
    color: #F8FAFC !important;
    font-size: 2.45rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.06rem;
}

.tm-page-description {
    margin: 0.7rem 0 1.7rem;
    color: #AAB8CE;
    font-size: 1.05rem;
}

.tm-info-card {
    padding: 1rem 1.15rem;
    border: 1px solid rgba(34, 211, 238, 0.20);
    border-radius: 16px;
    background: rgba(34, 211, 238, 0.06);
    color: #C9D7E8;
    line-height: 1.5;
}

.tm-ready-card {
    margin-top: 1.3rem;
    padding: 2rem 1.5rem;
    border: 1px solid rgba(103, 232, 249, 0.40);
    border-radius: 22px;
    background:
        radial-gradient(
            circle at 15% 5%,
            rgba(34, 211, 238, 0.15),
            transparent 40%
        ),
        linear-gradient(
            135deg,
            rgba(12, 46, 66, 0.86),
            rgba(28, 27, 69, 0.82)
        );
    box-shadow:
        0 18px 42px rgba(0, 0, 0, 0.20),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
    text-align: center;
}

.tm-ready-icon {
    font-size: 3rem;
}

.tm-ready-title {
    margin-top: 0.5rem;
    color: #FFFFFF;
    font-size: 1.55rem;
    font-weight: 800;
}

.tm-ready-text {
    margin-top: 0.55rem;
    color: #C8D7E9;
    font-size: 1rem;
    line-height: 1.6;
}

[data-testid="stForm"] {
    padding: 1.65rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 22px;
    background: rgba(15, 23, 42, 0.72);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
}

[data-testid="stWidgetLabel"] p {
    color: #D6E0EF !important;
    font-weight: 650;
}

.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stDateInput input {
    border: 1px solid rgba(148, 163, 184, 0.30) !important;
    border-radius: 12px !important;
    background: rgba(7, 11, 20, 0.68) !important;
    color: #F8FAFC !important;
}

.stTextInput input,
.stNumberInput input,
.stDateInput input {
    min-height: 46px;
}

.stTextArea textarea {
    min-height: 110px;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #72819A !important;
}

.stTextInput input:focus,
.stTextArea textarea:focus,
.stNumberInput input:focus,
.stDateInput input:focus {
    border-color: #22D3EE !important;
    box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.13) !important;
}

[data-baseweb="select"] > div {
    min-height: 46px;
    border-radius: 12px !important;
    background: rgba(7, 11, 20, 0.68) !important;
    border-color: rgba(148, 163, 184, 0.30) !important;
}

[data-baseweb="select"] * {
    color: #E5EDF8 !important;
}

.stRadio label {
    color: #D6E0EF !important;
}

.stMultiSelect [data-baseweb="tag"] {
    border-radius: 999px !important;
    background: rgba(34, 211, 238, 0.14) !important;
}

.stFormSubmitButton > button,
.stButton > button {
    width: 100%;
    min-height: 52px;
    border: 0 !important;
    border-radius: 13px !important;
    background: linear-gradient(
        135deg,
        #06B6D4 0%,
        #22D3EE 48%,
        #8B5CF6 100%
    ) !important;
    color: #FFFFFF !important;
    font-size: 1rem;
    font-weight: 750;
    box-shadow: 0 10px 25px rgba(34, 211, 238, 0.20);
    transition:
        transform 180ms ease,
        filter 180ms ease,
        box-shadow 180ms ease;
}

.stFormSubmitButton > button:hover,
.stButton > button:hover {
    transform: translateY(-2px);
    filter: brightness(1.08);
    box-shadow: 0 15px 30px rgba(34, 211, 238, 0.26);
}

[data-testid="stAlert"] {
    border-radius: 14px;
}

/* ----------------------------------------------------------
   ЯРКИЕ КНОПКИ НАВИГАЦИИ STREAMLIT
   ---------------------------------------------------------- */

section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"],
[data-testid="stPageLink-NavLink"] {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 48px !important;
    padding: 0.7rem 1rem !important;
    border: 1px solid rgba(234, 252, 255, 0.60) !important;
    border-radius: 14px !important;
    background:
        linear-gradient(
            135deg,
            #069FBE 0%,
            #1DCDE6 46%,
            #568DF0 72%,
            #8057E9 100%
        ) !important;
    color: #FFFFFF !important;
    text-decoration: none !important;
    font-size: 0.96rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.01rem !important;
    box-shadow:
        0 10px 22px rgba(34, 211, 238, 0.22),
        0 7px 18px rgba(139, 92, 246, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
    transition:
        transform 180ms ease,
        filter 180ms ease,
        box-shadow 180ms ease !important;
}

section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] p,
[data-testid="stPageLink-NavLink"] p {
    margin: 0 !important;
    color: #FFFFFF !important;
    font-size: 0.96rem !important;
    font-weight: 800 !important;
}

section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:hover,
[data-testid="stPageLink-NavLink"]:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.09) saturate(1.06) !important;
    box-shadow:
        0 16px 30px rgba(34, 211, 238, 0.29),
        0 12px 25px rgba(139, 92, 246, 0.21),
        inset 0 1px 0 rgba(255, 255, 255, 0.34) !important;
}

section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:focus-visible,
[data-testid="stPageLink-NavLink"]:focus-visible {
    outline: 3px solid rgba(125, 235, 250, 0.88) !important;
    outline-offset: 3px !important;
}

@media (max-width: 640px) {
    .block-container {
        padding: 1.8rem 1rem 3rem;
    }

    .tm-page-title {
        font-size: 2rem !important;
    }

    [data-testid="stForm"] {
        padding: 1.15rem;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

auth.render_main_menu_button()

st.markdown(
    '<div class="tm-page-eyebrow">TravelMind AI</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<h1 class="tm-page-title">✈️ Спланировать поездку</h1>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="tm-page-description">
        Расскажите о будущем путешествии — AI составит персональный маршрут,
        рассчитает примерный бюджет и предложит варианты проживания.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="tm-info-card">
        ✦ Используется пресет <b>{ai.PROMPT_VERSION}</b> ·
        модель <b>{st.secrets.get("LLM_MODEL", "deepseek-chat")}</b> ·
        максимальная длительность маршрута: <b>{ai.MAX_DAYS} дней</b>.
    </div>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# ЭКРАН ПОСЛЕ УСПЕШНОГО СОЗДАНИЯ МАРШРУТА
# ==========================================================

generated_trip_id = st.session_state.get("generated_trip_id")

if generated_trip_id:
    tokens_in = st.session_state.get("generated_tokens_in")
    tokens_out = st.session_state.get("generated_tokens_out")

    st.markdown(
        """
        <div class="tm-ready-card">
            <div class="tm-ready-icon">🗺️</div>
            <div class="tm-ready-title">Маршрут готов!</div>
            <div class="tm-ready-text">
                AI-маршрут сохранён в ваших путешествиях.
                Откройте его, чтобы посмотреть план по дням, карту,
                рекомендации и бюджет.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if tokens_in is not None and tokens_out is not None:
        st.caption(
            f"Использовано токенов: {tokens_in} вход / {tokens_out} выход."
        )

    st.write("")

    open_column, new_column = st.columns(2)

    with open_column:
        if st.button(
            "🗺️ Открыть готовый маршрут",
            type="primary",
            use_container_width=True,
            key="open_generated_trip",
        ):
            auth.remember_trip(int(generated_trip_id))

            st.session_state.pop("generated_trip_id", None)
            st.session_state.pop("generated_tokens_in", None)
            st.session_state.pop("generated_tokens_out", None)

            st.switch_page("pages/3_trip_detail.py")

    with new_column:
        if st.button(
            "✨ Создать ещё одну поездку",
            use_container_width=True,
            key="create_another_trip",
        ):
            st.session_state.pop("generated_trip_id", None)
            st.session_state.pop("generated_tokens_in", None)
            st.session_state.pop("generated_tokens_out", None)
            st.rerun()

    st.stop()

# ==========================================================
# ФОРМА СОЗДАНИЯ ПОЕЗДКИ
# ==========================================================

PACES = {
    "Спокойный": "slow",
    "Средний": "medium",
    "Насыщенный": "fast",
}

INTERESTS = [
    "история",
    "музеи",
    "архитектура",
    "искусство",
    "театры и концерты",
    "местная кухня",
    "рестораны высокой кухни",
    "кофейни и десерты",
    "уличная еда",
    "винные дегустации",
    "природа",
    "национальные парки",
    "озёра и водопады",
    "горы и треккинг",
    "море и пляжи",
    "активный спорт",
    "велосипедные маршруты",
    "экскурсии и гиды",
    "фотография",
    "видовые площадки",
    "шопинг",
    "рынки и локальные товары",
    "ночная жизнь",
    "бары и коктейли",
    "фестивали и события",
    "религиозные места",
    "современные районы",
    "уютные нетуристические места",
    "спа и wellness",
    "йога и медитация",
    "семейный отдых",
    "развлечения для детей",
    "романтические места",
    "бизнес и нетворкинг",
    "экология и осознанный туризм",
]

with st.form("plan_form"):
    st.subheader("📍 Основные параметры")

    column_1, column_2 = st.columns(2)

    with column_1:
        dest = st.text_input(
            "Куда отправляемся?",
            placeholder="Например: Стамбул, Турция",
        )

    with column_2:
        today = date.today()

        dates = st.date_input(
            "Даты поездки",
            value=(
                today + timedelta(days=14),
                today + timedelta(days=17),
            ),
            min_value=today,
            format="DD/MM/YYYY",
            help="Выберите дату начала и дату окончания поездки.",
        )

    st.write("")

    st.subheader("💳 Бюджет и формат поездки")

    column_3, column_4, column_5 = st.columns(3)

    with column_3:
        budget = st.number_input(
            "Общий бюджет",
            min_value=50,
            value=1000,
            step=50,
        )

    with column_4:
        curr = st.selectbox(
            "Валюта",
            ["USD", "EUR", "RUB"],
        )

    with column_5:
        people = st.number_input(
            "Путешественников",
            min_value=1,
            max_value=10,
            value=2,
        )

    style = st.selectbox(
        "Какой формат отдыха вам ближе?",
        [
            "Сбалансированный",
            "Бюджетный",
            "Комфорт / люкс",
            "Культурный",
            "Активный",
            "Гастрономический",
            "С детьми",
            "Романтический",
        ],
    )

    pace = st.radio(
        "Темп путешествия",
        list(PACES),
        index=1,
        horizontal=True,
    )

    st.write("")

    st.subheader("✨ Предпочтения")

    interests = st.multiselect(
        "Что вам интересно?",
        INTERESTS,
        default=["история", "местная кухня"],
        placeholder="Выберите интересы",
        help=(
            "Выберите несколько интересов — AI использует их при создании "
            "маршрута и подборе активностей."
        ),
    )

    notes = st.text_area(
        "Особые пожелания",
        placeholder=(
            "Например: без долгих пеших прогулок, "
            "вегетарианское питание, интересуют видовые площадки."
        ),
    )

    st.write("")

    submitted = st.form_submit_button(
        "✨ Создать маршрут с AI",
        use_container_width=True,
    )

if not submitted:
    st.stop()

# ==========================================================
# ВАЛИДАЦИЯ ВВОДА
# ==========================================================

if not dest.strip():
    st.error("Укажите направление поездки.")
    st.stop()

if not isinstance(dates, (list, tuple)) or len(dates) != 2:
    st.error("Выберите дату начала и дату окончания поездки.")
    st.stop()

start, end = dates
days = (end - start).days + 1

if days < 1 or days > ai.MAX_DAYS:
    st.error(
        f"Поездка должна длиться от 1 до {ai.MAX_DAYS} дней."
    )
    st.stop()

# ==========================================================
# СБОРКА ПРОМПТА
# ==========================================================

user_prompt = ai.build_prompt(
    dest=dest.strip(),
    start=start.isoformat(),
    end=end.isoformat(),
    days=days,
    budget=budget,
    curr=curr,
    people=people,
    style=style,
    pace=PACES[pace],
    interests=", ".join(interests) or "любые",
    notes=notes.strip() or "нет",
)

# ==========================================================
# ГЕНЕРАЦИЯ AI-МАРШРУТА
# ==========================================================

with st.spinner(
    "✦ AI анализирует предпочтения и составляет маршрут… "
    "обычно это занимает 20–60 секунд."
):
    try:
        result = ai.generate(user_prompt)

    except json.JSONDecodeError:
        st.error(
            "Модель вернула некорректный ответ. "
            "Пожалуйста, попробуйте ещё раз."
        )
        st.stop()

    except Exception as error:
        st.error(f"Ошибка обращения к AI-модели: {error}")
        st.stop()

data = result["data"]

# ==========================================================
# ПРОВЕРКА КАЧЕСТВА
# ==========================================================

for warning in ai.validate(data):
    st.warning(warning)

# ==========================================================
# СОХРАНЕНИЕ МАРШРУТА
# ==========================================================

trip_id = db.save_trip(
    user_id,
    {
        "title": data.get("title", "Поездка"),
        "destination": dest.strip(),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "budget": budget,
        "currency": curr,
        "people": people,
    },
    json.dumps(data, ensure_ascii=False),
)

db.init_expenses_from_plan(trip_id, data)

# Сохраняем данные между перезапусками Streamlit.
st.session_state["generated_trip_id"] = int(trip_id)
st.session_state["generated_tokens_in"] = result.get("tokens_in", 0)
st.session_state["generated_tokens_out"] = result.get("tokens_out", 0)

# Сохраняем созданную поездку как текущую.
auth.remember_trip(trip_id)

# На новом запуске появится экран с кнопкой открытия маршрута.
st.rerun()
