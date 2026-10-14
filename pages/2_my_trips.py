"""Страница истории поездок: список, открытие и удаление."""
import json
from html import escape

import streamlit as st

import auth
import db

st.set_page_config(
    page_title="Мои путешествия",
    page_icon="🧳",
    layout="wide",
)

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
    max-width: 1200px;
    padding-top: 2.5rem;
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

.tm-trip-cover {
    min-height: 155px;
    padding: 1.35rem;
    border: 1px solid rgba(255, 255, 255, 0.16);
    border-radius: 20px 20px 0 0;
    color: #FFFFFF;
    box-shadow:
        inset 0 -60px 65px rgba(3, 8, 22, 0.42),
        inset 0 1px 0 rgba(255, 255, 255, 0.10);
}

.tm-trip-cover-icon {
    margin-bottom: 0.55rem;
    font-size: 2rem;
}

.tm-trip-cover-title {
    color: #FFFFFF;
    font-size: 1.55rem;
    font-weight: 800;
    letter-spacing: -0.03rem;
}

.tm-trip-cover-place {
    margin-top: 0.3rem;
    color: rgba(245, 250, 255, 0.84);
    font-size: 0.95rem;
}

.tm-trip-body {
    min-height: 142px;
    padding: 1.25rem 1.35rem 1.35rem;
    border-right: 1px solid rgba(148, 163, 184, 0.18);
    border-bottom: 1px solid rgba(148, 163, 184, 0.18);
    border-left: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 0 0 20px 20px;
    background: rgba(15, 23, 42, 0.73);
}

.tm-trip-meta {
    color: #AAB8CE;
    font-size: 0.92rem;
    line-height: 1.6;
}

.tm-trip-budget {
    margin-top: 0.7rem;
    color: #EAF4FF;
    font-size: 1.08rem;
    font-weight: 700;
}

.tm-trip-budget span {
    color: #67E8F9;
}

.tm-empty {
    margin-top: 1rem;
    padding: 2.6rem 1.5rem;
    border: 1px solid rgba(34, 211, 238, 0.20);
    border-radius: 22px;
    background: rgba(15, 23, 42, 0.64);
    text-align: center;
}

.tm-empty-icon {
    font-size: 3rem;
}

.tm-empty-title {
    margin-top: 0.8rem;
    color: #F8FAFC;
    font-size: 1.4rem;
    font-weight: 750;
}

.tm-empty-text {
    margin-top: 0.45rem;
    color: #AAB8CE;
}

.stButton > button,
.stLinkButton > a {
    width: 100%;
    min-height: 44px;
    border: 0 !important;
    border-radius: 12px !important;
    background: linear-gradient(
        135deg,
        #06B6D4 0%,
        #22D3EE 48%,
        #8B5CF6 100%
    ) !important;
    color: #FFFFFF !important;
    font-size: 0.95rem;
    font-weight: 700;
    box-shadow: 0 10px 22px rgba(34, 211, 238, 0.16);
}

.stButton > button:hover,
.stLinkButton > a:hover {
    transform: translateY(-2px);
    filter: brightness(1.08);
}

[data-testid="stAlert"] {
    border-radius: 14px;
}

@media (max-width: 640px) {
    .block-container {
        padding: 1.8rem 1rem 3rem;
    }

    .tm-page-title {
        font-size: 2rem !important;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

THEMES = {
    "city": {
        "icon": "🏙️",
        "label": "Городское путешествие",
        "background": (
            "linear-gradient(135deg, #0B1D3A 0%, #145DA0 52%, #6D28D9 100%)"
        ),
    },
    "mountains": {
        "icon": "🏔️",
        "label": "Горное путешествие",
        "background": (
            "linear-gradient(135deg, #102A43 0%, #1F6F78 48%, #5C3D99 100%)"
        ),
    },
    "beach": {
        "icon": "🏖️",
        "label": "Отдых у моря",
        "background": (
            "linear-gradient(135deg, #075985 0%, #0891B2 45%, #F59E0B 100%)"
        ),
    },
    "culture": {
        "icon": "🏛️",
        "label": "Культурный маршрут",
        "background": (
            "linear-gradient(135deg, #3F1D2E 0%, #8B4513 50%, #D97706 100%)"
        ),
    },
    "food": {
        "icon": "🍜",
        "label": "Гастрономическое путешествие",
        "background": (
            "linear-gradient(135deg, #4C1D1D 0%, #B45309 48%, #EAB308 100%)"
        ),
    },
    "nature": {
        "icon": "🌲",
        "label": "Путешествие на природу",
        "background": (
            "linear-gradient(135deg, #052E16 0%, #15803D 48%, #0F766E 100%)"
        ),
    },
    "adventure": {
        "icon": "🧭",
        "label": "Активное приключение",
        "background": (
            "linear-gradient(135deg, #3B0764 0%, #7E22CE 48%, #DB2777 100%)"
        ),
    },
    "mixed": {
        "icon": "✈️",
        "label": "Новое путешествие",
        "background": (
            "linear-gradient(135deg, #0F172A 0%, #0E7490 50%, #6D28D9 100%)"
        ),
    },
}


def get_trip_theme(trip: dict) -> dict:
    """Определяет тему обложки из JSON маршрута или по названию поездки."""
    theme_key = ""

    raw_data = trip.get("data")

    if raw_data:
        try:
            trip_data = json.loads(raw_data)
            theme_key = str(trip_data.get("cover_theme", "")).lower()
        except (json.JSONDecodeError, TypeError):
            theme_key = ""

    if theme_key in THEMES:
        return THEMES[theme_key]

    text = (
        f"{trip.get('title', '')} "
        f"{trip.get('destination', '')}"
    ).lower()

    if any(word in text for word in ["горы", "эльбрус", "алтай", "кавказ"]):
        return THEMES["mountains"]

    if any(word in text for word in ["море", "пляж", "сочи", "бали", "турция"]):
        return THEMES["beach"]

    if any(word in text for word in ["еда", "кухня", "ресторан", "гастро"]):
        return THEMES["food"]

    if any(word in text for word in ["лес", "озеро", "парк", "природ"]):
        return THEMES["nature"]

    if any(word in text for word in ["музей", "истор", "культур", "архитект"]):
        return THEMES["culture"]

    return THEMES["city"]


st.markdown(
    '<div class="tm-page-eyebrow">TravelMind AI</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<h1 class="tm-page-title">🧳 Мои путешествия</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="tm-page-description">
        Здесь хранятся созданные AI-маршруты, бюджеты и планы ваших будущих поездок.
    </div>
    """,
    unsafe_allow_html=True,
)

trips = db.list_trips(user_id)

if not trips:
    st.markdown(
        """
        <div class="tm-empty">
            <div class="tm-empty-icon">✈️</div>
            <div class="tm-empty-title">Путешествий пока нет</div>
            <div class="tm-empty-text">
                Создайте первую поездку — TravelMind подготовит маршрут за несколько минут.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    st.page_link(
        "pages/1_new_trip.py",
        label="✨ Спланировать первую поездку",
        use_container_width=True,
    )

    st.stop()

st.caption(f"Всего сохранённых путешествий: {len(trips)}")

st.write("")

for trip in trips:
    theme = get_trip_theme(trip)

    title = escape(str(trip.get("title", "Поездка")))
    destination = escape(str(trip.get("destination", "")))
    start_date = escape(str(trip.get("start_date", "")))
    end_date = escape(str(trip.get("end_date", "")))
    people = trip.get("people", 1)
    budget = float(trip.get("budget", 0) or 0)
    currency = escape(str(trip.get("currency", "")))

    st.markdown(
        f"""
        <div class="tm-trip-cover" style="background: {theme["background"]};">
            <div class="tm-trip-cover-icon">{theme["icon"]}</div>
            <div class="tm-trip-cover-title">{title}</div>
            <div class="tm-trip-cover-place">
                {theme["label"]} · {destination}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="tm-trip-body">
            <div class="tm-trip-meta">
                📅 {start_date} — {end_date}<br>
                👥 Путешественников: {people}
            </div>
            <div class="tm-trip-budget">
                Бюджет: <span>{budget:.0f} {currency}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    action_1, action_2 = st.columns([3, 1])

    with action_1:
        if st.button(
            "🗺️ Открыть маршрут",
            key=f"open_{trip['id']}",
            use_container_width=True,
        ):
            st.session_state["current_trip_id"] = trip["id"]
            st.switch_page("pages/3_trip_detail.py")

    with action_2:
        if st.button(
            "🗑️ Удалить",
            key=f"delete_{trip['id']}",
            use_container_width=True,
        ):
            db.delete_trip(trip["id"], user_id)
            st.toast(f"Поездка «{trip['title']}» удалена")
            st.rerun()

    st.write("")
