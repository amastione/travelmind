"""Детали поездки: маршрут, карта, расходы, советы и экспорт."""
import json
from collections import defaultdict
from datetime import date
from html import escape
from urllib.parse import quote_plus

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import ai
import auth
import db

st.set_page_config(
    page_title="Маршрут поездки",
    page_icon="🗺️",
    layout="wide",
)

# ---------- АВТОРИЗАЦИЯ И ПОЛУЧЕНИЕ ПОЕЗДКИ ----------

user_id = auth.require_auth()
trip_id = st.session_state.get("current_trip_id")

if not trip_id:
    st.warning("Поездка не выбрана. Откройте её из списка путешествий.")
    st.page_link(
        "pages/2_my_trips.py",
        label="🧳 Перейти к моим путешествиям",
        use_container_width=True,
    )
    st.stop()

trip = db.get_trip(trip_id, user_id)

if not trip:
    st.error("Поездка не найдена или была удалена.")
    st.page_link(
        "pages/2_my_trips.py",
        label="🧳 Перейти к моим путешествиям",
        use_container_width=True,
    )
    st.stop()

try:
    data = json.loads(trip["data"])
except (json.JSONDecodeError, TypeError):
    st.error("Не удалось прочитать данные маршрута.")
    st.stop()

curr = trip["currency"]

# ---------- СТИЛИ ----------

CSS = """
<style>
.stApp {
    background:
        radial-gradient(
            circle at 8% 6%,
            rgba(34, 211, 238, 0.14),
            transparent 27%
        ),
        radial-gradient(
            circle at 91% 85%,
            rgba(139, 92, 246, 0.18),
            transparent 34%
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
    max-width: 1220px;
    padding-top: 2.3rem;
    padding-bottom: 4rem;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

h1, h2, h3, h4 {
    color: #F8FAFC !important;
}

.tm-back-link {
    margin-bottom: 1.2rem;
}

.tm-back-link a {
    color: #9CECF8;
    text-decoration: none;
    font-weight: 650;
}

.tm-back-link a:hover {
    color: #FFFFFF;
}

.tm-hero {
    position: relative;
    overflow: hidden;
    margin-bottom: 1.3rem;
    padding: 2rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 24px;
    background:
        radial-gradient(
            circle at 88% 20%,
            rgba(34, 211, 238, 0.25),
            transparent 28%
        ),
        radial-gradient(
            circle at 82% 92%,
            rgba(139, 92, 246, 0.28),
            transparent 36%
        ),
        linear-gradient(
            135deg,
            rgba(9, 23, 43, 0.92),
            rgba(19, 27, 54, 0.88)
        );
    box-shadow: 0 20px 55px rgba(0, 0, 0, 0.22);
}

.tm-hero::after {
    content: "✦";
    position: absolute;
    right: 2.1rem;
    top: 1.1rem;
    color: rgba(103, 232, 249, 0.30);
    font-size: 6rem;
    line-height: 1;
}

.tm-eyebrow {
    position: relative;
    z-index: 1;
    color: #67E8F9;
    font-size: 0.78rem;
    font-weight: 750;
    letter-spacing: 0.10rem;
    text-transform: uppercase;
}

.tm-hero-title {
    position: relative;
    z-index: 1;
    max-width: 820px;
    margin: 0.5rem 0 0;
    color: #F8FAFC;
    font-size: 2.35rem;
    font-weight: 820;
    line-height: 1.12;
    letter-spacing: -0.06rem;
}

.tm-hero-meta {
    position: relative;
    z-index: 1;
    margin-top: 0.85rem;
    color: #C2D0E3;
    font-size: 1rem;
    line-height: 1.6;
}

.tm-hero-overview {
    position: relative;
    z-index: 1;
    max-width: 850px;
    margin: 1rem 0 0;
    color: #AEBED3;
    line-height: 1.65;
}

.tm-mood {
    position: relative;
    z-index: 1;
    display: inline-block;
    margin-top: 1rem;
    padding: 0.45rem 0.8rem;
    border: 1px solid rgba(250, 204, 21, 0.24);
    border-radius: 999px;
    background: rgba(250, 204, 21, 0.08);
    color: #FDE68A;
    font-size: 0.88rem;
}

[data-testid="stMetric"] {
    min-height: 116px;
    padding: 1rem 1.15rem;
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 17px;
    background: rgba(15, 23, 42, 0.68);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.14);
}

[data-testid="stMetricLabel"] {
    color: #9EADC3 !important;
    font-size: 0.85rem !important;
}

[data-testid="stMetricValue"] {
    color: #F8FAFC !important;
}

[data-testid="stMetricDelta"] {
    font-size: 0.78rem !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.45rem;
    margin-top: 1.5rem;
    padding: 0.42rem;
    border: 1px solid rgba(148, 163, 184, 0.17);
    border-radius: 16px;
    background: rgba(15, 23, 42, 0.58);
}

.stTabs [data-baseweb="tab"] {
    height: 46px;
    padding: 0 1rem;
    border-radius: 11px;
    color: #AAB8CE;
    font-weight: 650;
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(
        135deg,
        rgba(34, 211, 238, 0.18),
        rgba(139, 92, 246, 0.22)
    ) !important;
    color: #F8FAFC !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

.tm-section-title {
    margin: 1.25rem 0 0.35rem;
    color: #F8FAFC;
    font-size: 1.4rem;
    font-weight: 750;
}

.tm-section-description {
    margin-bottom: 1.1rem;
    color: #AAB8CE;
    line-height: 1.55;
}

.tm-hotel-card {
    min-height: 330px;
    padding: 1.15rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 18px;
    background: rgba(15, 23, 42, 0.72);
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.13);
}

.tm-hotel-tier {
    display: inline-block;
    padding: 0.36rem 0.62rem;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.07rem;
}

.tm-hotel-name {
    margin: 0.85rem 0 0;
    color: #F8FAFC;
    font-size: 1.18rem;
    font-weight: 750;
    line-height: 1.35;
}

.tm-hotel-area {
    margin-top: 0.4rem;
    color: #AAB8CE;
    font-size: 0.9rem;
}

.tm-hotel-rating {
    margin-top: 0.7rem;
    color: #FDE68A;
    font-size: 0.92rem;
    font-weight: 650;
}

.tm-hotel-description {
    min-height: 65px;
    margin-top: 0.75rem;
    color: #C6D2E2;
    font-size: 0.9rem;
    line-height: 1.55;
}

.tm-hotel-price {
    margin-top: 0.8rem;
    padding: 0.7rem;
    border-radius: 11px;
    background: rgba(34, 211, 238, 0.07);
    color: #D9F9FF;
    font-size: 0.88rem;
}

.tm-day-note {
    margin: 0.45rem 0 1rem;
    color: #AAB8CE;
    font-size: 0.92rem;
}

.streamlit-expanderHeader {
    border: 1px solid rgba(148, 163, 184, 0.18) !important;
    border-radius: 14px !important;
    background: rgba(15, 23, 42, 0.70) !important;
    color: #F8FAFC !important;
    font-weight: 700 !important;
}

.tm-activity {
    margin: 0.8rem 0;
    padding: 1rem;
    border-left: 3px solid #22D3EE;
    border-radius: 0 14px 14px 0;
    background: rgba(13, 30, 54, 0.55);
}

.tm-activity-time {
    color: #67E8F9;
    font-size: 0.83rem;
    font-weight: 750;
    letter-spacing: 0.03rem;
}

.tm-activity-title {
    margin-top: 0.18rem;
    color: #F8FAFC;
    font-size: 1.03rem;
    font-weight: 720;
}

.tm-activity-info {
    margin-top: 0.3rem;
    color: #B5C4D8;
    font-size: 0.89rem;
    line-height: 1.55;
}

.tm-activity-description {
    margin-top: 0.45rem;
    color: #CED9E7;
    font-size: 0.9rem;
    line-height: 1.55;
}

.tm-day-total {
    margin-top: 0.85rem;
    padding: 0.75rem 0.9rem;
    border-radius: 12px;
    background: rgba(139, 92, 246, 0.12);
    color: #E5D5FF;
    font-weight: 700;
}

.tm-map-card {
    margin-top: 1.1rem;
    padding: 0.6rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 18px;
    background: rgba(15, 23, 42, 0.66);
    overflow: hidden;
}

.tm-tip-card {
    margin: 0.65rem 0;
    padding: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 14px;
    background: rgba(15, 23, 42, 0.65);
    color: #C8D5E5;
    line-height: 1.55;
}

.stButton > button,
.stLinkButton > a,
.stDownloadButton > button {
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
    font-size: 0.94rem;
    font-weight: 720;
    box-shadow: 0 10px 22px rgba(34, 211, 238, 0.16);
}

.stButton > button:hover,
.stLinkButton > a:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    filter: brightness(1.08);
}

.stNumberInput input {
    border: 1px solid rgba(148, 163, 184, 0.30) !important;
    border-radius: 10px !important;
    background: rgba(7, 11, 20, 0.68) !important;
    color: #F8FAFC !important;
}

[data-testid="stAlert"] {
    border-radius: 14px;
}

[data-testid="stDataFrame"] {
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 14px;
    overflow: hidden;
}

@media (max-width: 760px) {
    .block-container {
        padding: 1.6rem 1rem 3rem;
    }

    .tm-hero {
        padding: 1.35rem;
    }

    .tm-hero-title {
        font-size: 1.8rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        overflow-x: auto;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ---------- СЛОВАРИ ----------

ICONS = {
    "A": "🏛️",
    "F": "🍽️",
    "T": "🚌",
    "S": "🏨",
    "L": "🌿",
    "H": "🛍️",
    "W": "✨",
}

COLORS = {
    "A": "blue",
    "F": "orange",
    "T": "gray",
    "S": "purple",
    "L": "green",
    "H": "pink",
    "W": "red",
}

BUDGET_RU = {
    "accommodation": "Проживание",
    "food": "Еда",
    "activities": "Активности",
    "transport": "Транспорт",
    "other": "Прочее",
}

TIP_RU = {
    "transport": "🚌 Транспорт",
    "safety": "🛡️ Безопасность",
    "culture": "🎭 Культура",
    "money": "💳 Деньги",
}

TIER_STYLES = {
    "Эконом": {
        "label": "ЭКОНОМ",
        "color": "#38BDF8",
        "background": "rgba(56, 189, 248, 0.12)",
        "emoji": "💎",
    },
    "Оптимальный": {
        "label": "ОПТИМАЛЬНЫЙ",
        "color": "#34D399",
        "background": "rgba(52, 211, 153, 0.12)",
        "emoji": "⭐",
    },
    "Премиум": {
        "label": "ПРЕМИУМ",
        "color": "#A78BFA",
        "background": "rgba(167, 139, 250, 0.12)",
        "emoji": "👑",
    },
}


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------

def safe_float(value, default=0.0):
    """Преобразует значение в число без ошибки."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# ---------- ШАПКА ----------

trip_title = escape(str(data.get("title") or trip["title"] or "Поездка"))
destination = escape(str(trip["destination"] or ""))
start_date_text = escape(str(trip["start_date"] or ""))
end_date_text = escape(str(trip["end_date"] or ""))
people = trip["people"] or 1
overview = escape(str(data.get("overview") or ""))

st.markdown(
    """
    <div class="tm-back-link">
        <a href="/Мои_путешествия">← Вернуться к списку путешествий</a>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"""
    <div class="tm-hero">
        <div class="tm-eyebrow">TravelMind AI · Персональный маршрут</div>
        <div class="tm-hero-title">{trip_title}</div>
        <div class="tm-hero-meta">
            📍 {destination}<br>
            📅 {start_date_text} — {end_date_text} · 👥 {people} чел.
        </div>
        <div class="tm-hero-overview">{overview}</div>
    """,
    unsafe_allow_html=True,
)

if data.get("mood_reason"):
    mood_reason = escape(str(data.get("mood_reason")))
    st.markdown(
        f'<div class="tm-mood">🙂 {mood_reason}</div>',
        unsafe_allow_html=True,
    )

st.markdown("</div>", unsafe_allow_html=True)

# ---------- МЕТРИКИ ----------

expenses = db.get_expenses(trip_id)

plan_sum = sum((expense["cost_plan"] or 0) for expense in expenses)
actual_sum = sum((expense["cost_actual"] or 0) for expense in expenses)

total_cost = safe_float(data.get("total_cost"), plan_sum)
if total_cost <= 0:
    total_cost = plan_sum

actual_delta = None
if actual_sum:
    actual_delta = f"{actual_sum - plan_sum:+.0f} {curr}"

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

metric_1.metric("Плановый бюджет", f"{total_cost:.0f} {curr}")
metric_2.metric(
    "Фактические расходы",
    f"{actual_sum:.0f} {curr}",
    delta=actual_delta,
)
metric_3.metric("Ожидаемые эмоции", f"{data.get('mood_score', '—')}/10")
metric_4.metric("Дней в маршруте", len(data.get("days", [])))

# ---------- ВКЛАДКИ ----------

tabs = st.tabs(
    [
        "📅 Маршрут по дням",
        "🗺️ Карта поездки",
        "💳 Бюджет и расходы",
        "💡 Советы",
        "🤖 Данные AI",
    ]
)

# ---------- ВКЛАДКА 1: МАРШРУТ ----------

with tabs[0]:
    hotels = data.get("hotels") or []

    if hotels:
        st.markdown(
            '<div class="tm-section-title">🏨 Где остановиться</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="tm-section-description">
                Варианты проживания от AI. Цены являются ориентировочными:
                перед бронированием проверьте актуальную стоимость и наличие
                мест в официальном сервисе отеля или бронирования.
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            trip_start = date.fromisoformat(str(trip["start_date"]))
            trip_end = date.fromisoformat(str(trip["end_date"]))
            nights = max((trip_end - trip_start).days, 1)
        except (TypeError, ValueError):
            nights = max(len(data.get("days", [])) - 1, 1)

        hotel_columns = st.columns(3)

        for index, hotel in enumerate(hotels[:3]):
            tier = hotel.get("tier", "Оптимальный")
            style = TIER_STYLES.get(tier, TIER_STYLES["Оптимальный"])

            hotel_name = escape(str(hotel.get("name", "Вариант проживания")))
            hotel_area = escape(str(hotel.get("area", "Удобный район")))
            hotel_why = escape(str(hotel.get("why", "")))
            rating = safe_float(hotel.get("rating"), 0)

            rooms = hotel.get("rooms") or {}
            standard_price = safe_float(rooms.get("standard"), 0)
            total_stay = standard_price * nights

            map_query = str(
                hotel.get(
                    "map_query",
                    f"{hotel.get('name', '')} {trip['destination']}",
                )
            )

            google_maps_url = (
                "https://www.google.com/maps/search/?api=1&query="
                + quote_plus(map_query)
            )

            with hotel_columns[index]:
                st.markdown(
                    f"""
                    <div class="tm-hotel-card">
                        <div
                            class="tm-hotel-tier"
                            style="
                                color: {style["color"]};
                                background: {style["background"]};
                                border: 1px solid {style["color"]};
                            "
                        >
                            {style["emoji"]} {style["label"]}
                        </div>

                        <div class="tm-hotel-name">{hotel_name}</div>
                        <div class="tm-hotel-area">📍 {hotel_area}</div>

                        <div class="tm-hotel-rating">
                            {"⭐ Рейтинг: " + f"{rating:.1f}/10" if rating else "⭐ Рейтинг уточняется"}
                        </div>

                        <div class="tm-hotel-description">
                            {hotel_why or "Вариант проживания в удобной локации для вашего маршрута."}
                        </div>

                        <div class="tm-hotel-price">
                            Стандартный номер: примерно
                            <b>{total_stay:.0f} {curr}</b> за {nights} ноч.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.link_button(
                    "📍 Открыть на карте",
                    google_maps_url,
                    use_container_width=True,
                )

        st.divider()

    accommodation = data.get("accommodation") or {}

    if not hotels and isinstance(accommodation, dict) and accommodation:
        accommodation_type = escape(str(accommodation.get("type", "")))
        accommodation_area = escape(str(accommodation.get("area", "")))
        accommodation_why = escape(str(accommodation.get("why", "")))
        accommodation_price = safe_float(
            accommodation.get("price_per_night"),
            0,
        )

        st.info(
            f"🏨 Проживание: {accommodation_type} "
            f"в районе {accommodation_area} · "
            f"примерно {accommodation_price:.0f} {curr}/ночь. "
            f"{accommodation_why}"
        )

    elif not hotels and isinstance(accommodation, list) and accommodation:
        st.markdown(
            '<div class="tm-section-title">🏨 Варианты проживания</div>',
            unsafe_allow_html=True,
        )

        for hotel in accommodation:
            hotel_name = escape(str(hotel.get("name", "Вариант проживания")))
            hotel_tier = escape(str(hotel.get("tier", "")))
            hotel_area = escape(str(hotel.get("area", "")))
            hotel_why = escape(str(hotel.get("why", "")))
            hotel_price = safe_float(hotel.get("price_per_night"), 0)

            with st.container(border=True):
                hotel_left, hotel_right = st.columns([3, 1])

                with hotel_left:
                    st.markdown(f"### {hotel_name}")
                    st.caption(f"Категория: {hotel_tier}")
                    st.write(f"📍 Район: {hotel_area}")
                    st.write(hotel_why)

                with hotel_right:
                    st.metric("За ночь", f"{hotel_price:.0f} {curr}")

    st.markdown(
        '<div class="tm-section-title">📅 План путешествия</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tm-section-description">Маршрут составлен так, чтобы активности удобно сочетались по времени и расположению.</div>',
        unsafe_allow_html=True,
    )

    for day in data.get("days", []):
        day_number = day.get("day", "")
        day_date = day.get("date", "")
        day_theme = day.get("theme", "")
        day_vibe = day.get("vibe", "")

        header = f"День {day_number} · {day_date}"
        if day_theme:
            header += f" — {day_theme}"
        if day_vibe:
            header += f" · {day_vibe}"

        with st.expander(header, expanded=(day_number == 1)):
            if day_theme or day_vibe:
                st.markdown(
                    f"""
                    <div class="tm-day-note">
                        {escape(str(day_theme))} · {escape(str(day_vibe))}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            activities = day.get("activities") or []

            if not activities:
                st.info("Для этого дня пока нет активностей.")
                continue

            for activity in activities:
                activity_type = activity.get("type", "")
                icon = ICONS.get(activity_type, "📍")

                time_value = escape(str(activity.get("time", "")))
                title = escape(str(activity.get("title", "")))
                duration = escape(str(activity.get("duration_min", "?")))
                cost = safe_float(activity.get("cost"), 0)
                location = escape(str(activity.get("location", "")))
                description = escape(str(activity.get("description", "")))
                tip = escape(str(activity.get("tip", "")))

                st.markdown(
                    f"""
                    <div class="tm-activity">
                        <div class="tm-activity-time">
                            {time_value} · {icon} · ~{cost:.0f} {curr}
                        </div>
                        <div class="tm-activity-title">{title}</div>
                        <div class="tm-activity-info">
                            ⏱️ {duration} мин · 📍 {location}
                        </div>
                        <div class="tm-activity-description">
                            {description}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if tip:
                    st.caption(f"💡 {tip}")

            day_cost = safe_float(day.get("day_cost"), 0)

            st.markdown(
                f"""
                <div class="tm-day-total">
                    Итого за день: ~{day_cost:.0f} {curr}
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------- ВКЛАДКА 2: КАРТА ----------

with tabs[1]:
    st.markdown(
        '<div class="tm-section-title">🗺️ Карта маршрута</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="tm-section-description">
            Метки показывают места, рекомендованные в плане поездки.
            Линии объединяют активности в рамках одного дня.
        </div>
        """,
        unsafe_allow_html=True,
    )

    points = []

    for day in data.get("days", []):
        for activity in day.get("activities", []):
            lat = activity.get("lat")
            lon = activity.get("lon")

            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                points.append(
                    (
                        lat,
                        lon,
                        activity,
                        day.get("day"),
                    )
                )

    if not points:
        st.info("Для этой поездки AI не вернул координаты мест для построения карты.")

    else:
        center = [
            sum(point[0] for point in points) / len(points),
            sum(point[1] for point in points) / len(points),
        ]

        fmap = folium.Map(
            location=center,
            zoom_start=12,
            tiles="OpenStreetMap",
            attr="© OpenStreetMap contributors",
            max_zoom=19,
            attribution_control=False,
        )

        for lat, lon, activity, day_number in points:
            activity_type = activity.get("type", "")
            color = COLORS.get(activity_type, "blue")

            activity_title = escape(str(activity.get("title", "")))
            activity_time = escape(str(activity.get("time", "")))
            activity_location = escape(str(activity.get("location", "")))

            popup_html = (
                f"День {day_number} · {activity_time}<br>"
                f"<b>{activity_title}</b><br>"
                f"{activity_location}"
            )

            folium.Marker(
                location=[lat, lon],
                popup=popup_html,
                tooltip=activity.get("title", ""),
                icon=folium.Icon(
                    color=color,
                    icon="info-sign",
                ),
            ).add_to(fmap)

        points_by_day = defaultdict(list)

        for lat, lon, activity, day_number in points:
            points_by_day[day_number].append([lat, lon])

        for day_points in points_by_day.values():
            if len(day_points) > 1:
                folium.PolyLine(
                    day_points,
                    weight=3,
                    opacity=0.75,
                    color="#22D3EE",
                ).add_to(fmap)

        st.markdown('<div class="tm-map-card">', unsafe_allow_html=True)

        st_folium(
            fmap,
            use_container_width=True,
            height=520,
            returned_objects=[],
        )

        st.markdown("</div>", unsafe_allow_html=True)

        st.caption("Картографические данные: © OpenStreetMap contributors")

# ---------- ВКЛАДКА 3: БЮДЖЕТ ----------

with tabs[2]:
    st.markdown(
        '<div class="tm-section-title">💳 Бюджет и фактические расходы</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="tm-section-description">
            Добавляйте реальные траты во время путешествия. После сохранения
            сервис автоматически рассчитает отклонение от запланированного бюджета.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not expenses:
        st.info("Для этой поездки пока нет запланированных расходов.")

    else:
        for expense in expenses:
            expense_columns = st.columns([4, 1.15, 1.7, 0.8])

            day_number = expense["day"]
            category = expense["category"]
            title = expense["title"]
            plan_cost = safe_float(expense["cost_plan"], 0)
            actual_cost = safe_float(expense["cost_actual"], 0)

            with expense_columns[0]:
                st.markdown(
                    f"**День {day_number} · {ICONS.get(category, '•')} {title}**"
                )

            with expense_columns[1]:
                st.caption("План")
                st.write(f"{plan_cost:.0f} {curr}")

            with expense_columns[2]:
                actual_value = st.number_input(
                    "Факт",
                    min_value=0.0,
                    value=actual_cost,
                    step=10.0,
                    key=f"actual_{expense['id']}",
                    label_visibility="collapsed",
                )

            with expense_columns[3]:
                if st.button("💾", key=f"save_{expense['id']}"):
                    db.update_expense_actual(expense["id"], actual_value)
                    st.toast("Расход сохранён")
                    st.rerun()

            st.divider()

    budget_breakdown = data.get("budget_breakdown") or {}

    if budget_breakdown:
        st.markdown(
            '<div class="tm-section-title">📊 Структура планового бюджета</div>',
            unsafe_allow_html=True,
        )

        chart_data = pd.DataFrame(
            {
                "Категория": [
                    BUDGET_RU.get(key, key)
                    for key in budget_breakdown.keys()
                ],
                "План": pd.to_numeric(
                    list(budget_breakdown.values()),
                    errors="coerce",
                ),
            }
        ).fillna(0)

        chart_data = chart_data.set_index("Категория")

        st.bar_chart(chart_data)
        st.dataframe(chart_data, use_container_width=True)

        total_by_categories = chart_data["План"].sum()

        st.caption(
            f"Сумма по категориям: {total_by_categories:.0f} {curr}"
        )

# ---------- ВКЛАДКА 4: СОВЕТЫ ----------

with tabs[3]:
    st.markdown(
        '<div class="tm-section-title">💡 Полезное для поездки</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="tm-section-description">Сохраните важные рекомендации, отметьте вещи в чек-листе и используйте полезные фразы в путешествии.</div>',
        unsafe_allow_html=True,
    )

    wow_moments = data.get("wow_moments") or []

    if wow_moments:
        st.subheader("✨ Главные впечатления")

        for moment in wow_moments:
            st.markdown(
                f'<div class="tm-tip-card">✨ {escape(str(moment))}</div>',
                unsafe_allow_html=True,
            )

    packing = data.get("packing") or []

    if packing:
        st.subheader("🎒 Что взять с собой")

        for index, item in enumerate(packing):
            st.checkbox(
                str(item),
                key=f"packing_{trip_id}_{index}",
            )

    phrases = data.get("phrases") or []

    if phrases:
        st.subheader("💬 Полезные фразы")

        for phrase in phrases:
            russian = escape(str(phrase.get("ru", "")))
            local = escape(str(phrase.get("local", "")))

            st.markdown(
                f"""
                <div class="tm-tip-card">
                    <b>{russian}</b><br>
                    <span style="color: #67E8F9;">{local}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    tips = data.get("tips") or {}

    if tips:
        st.subheader("🧭 Советы путешественнику")

        for key, value in tips.items():
            tip_title = TIP_RU.get(key, key)
            tip_text = escape(str(value))

            st.markdown(
                f"""
                <div class="tm-tip-card">
                    <b>{tip_title}</b><br>
                    {tip_text}
                </div>
                """,
                unsafe_allow_html=True,
            )

# ---------- ВКЛАДКА 5: AI-ДАННЫЕ И ЭКСПОРТ ----------

with tabs[4]:
    st.markdown(
        '<div class="tm-section-title">🤖 Данные AI-маршрута</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="tm-section-description">
            Здесь отображается структурированный JSON-результат генерации.
            Его можно скачать для отчёта по проекту или дальнейшей обработки.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.json(data)

    download_markdown, download_json = st.columns(2)

    markdown_content = ai.to_markdown(data, curr)
    json_content = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )

    with download_markdown:
        st.download_button(
            label="⬇️ Скачать маршрут в Markdown",
            data=markdown_content,
            file_name=f"travelmind_trip_{trip_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with download_json:
        st.download_button(
            label="⬇️ Скачать маршрут в JSON",
            data=json_content,
            file_name=f"travelmind_trip_{trip_id}.json",
            mime="application/json",
            use_container_width=True,
        )
