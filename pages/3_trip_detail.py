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

# ==========================================================
# АВТОРИЗАЦИЯ И ПОЛУЧЕНИЕ ДАННЫХ ПОЕЗДКИ
# ==========================================================

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

curr = trip["currency"] or "RUB"

# ==========================================================
# СТИЛИ TRAVELMIND
# ==========================================================

CSS = """
<style>
.stApp {
    background:
        radial-gradient(
            circle at 8% 7%,
            rgba(34, 211, 238, 0.14),
            transparent 28%
        ),
        radial-gradient(
            circle at 92% 88%,
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
    max-width: 1220px;
    padding-top: 2.1rem;
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

.tm-hero {
    margin-bottom: 1.3rem;
    padding: 1.85rem 2rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 24px;
    background:
        radial-gradient(
            circle at 92% 14%,
            rgba(34, 211, 238, 0.20),
            transparent 28%
        ),
        radial-gradient(
            circle at 82% 100%,
            rgba(139, 92, 246, 0.25),
            transparent 36%
        ),
        linear-gradient(
            135deg,
            rgba(9, 23, 43, 0.96),
            rgba(19, 27, 54, 0.90)
        );
    box-shadow: 0 20px 55px rgba(0, 0, 0, 0.22);
}

.tm-eyebrow {
    margin-bottom: 0.4rem;
    color: #67E8F9;
    font-size: 0.8rem;
    font-weight: 750;
    letter-spacing: 0.1rem;
    text-transform: uppercase;
}

.tm-hero-title {
    margin-top: 0.15rem;
    color: #F8FAFC;
    font-size: 2.35rem;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.06rem;
}

.tm-hero-meta {
    margin-top: 0.8rem;
    color: #C2D0E3;
    font-size: 1rem;
    line-height: 1.6;
}

.tm-hero-overview {
    margin-top: 0.9rem;
    color: #AEBED3;
    font-size: 1rem;
    line-height: 1.65;
}

.tm-mood {
    margin-top: 0.95rem;
    color: #FDE68A;
    font-size: 0.9rem;
}

[data-testid="stMetric"] {
    min-height: 125px;
    padding: 1rem 1.1rem;
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 17px;
    background: rgba(15, 23, 42, 0.70);
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

/* ---------- ВКЛАДКИ МАРШРУТА ---------- */

.stTabs [data-baseweb="tab-list"] {
    gap: 0.65rem;
    margin-top: 1.7rem;
    margin-bottom: 0.7rem;
    padding: 0.65rem;
    border: 1px solid rgba(103, 232, 249, 0.20);
    border-radius: 20px;
    background:
        linear-gradient(
            135deg,
            rgba(15, 23, 42, 0.92),
            rgba(20, 29, 55, 0.88)
        );
    box-shadow:
        0 14px 34px rgba(0, 0, 0, 0.18),
        inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.stTabs [data-baseweb="tab"] {
    min-height: 52px;
    padding: 0.65rem 1.1rem;
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-radius: 14px;
    background: rgba(7, 11, 20, 0.42);
    color: #C6D2E2;
    font-size: 0.95rem;
    font-weight: 720;
    transition:
        background 0.2s ease,
        border-color 0.2s ease,
        color 0.2s ease,
        transform 0.2s ease;
}

.stTabs [data-baseweb="tab"]:hover {
    border-color: rgba(103, 232, 249, 0.52);
    background: rgba(34, 211, 238, 0.10);
    color: #F8FAFC;
    transform: translateY(-1px);
}

.stTabs [aria-selected="true"] {
    border-color: rgba(125, 211, 252, 0.62) !important;
    background:
        linear-gradient(
            135deg,
            rgba(6, 182, 212, 0.88) 0%,
            rgba(34, 211, 238, 0.78) 48%,
            rgba(139, 92, 246, 0.86) 100%
        ) !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    box-shadow:
        0 8px 20px rgba(34, 211, 238, 0.20),
        inset 0 1px 0 rgba(255, 255, 255, 0.26);
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none;
}

.tm-section-title {
    margin-top: 1.25rem;
    margin-bottom: 0.35rem;
    color: #F8FAFC;
    font-size: 1.45rem;
    font-weight: 750;
}

.tm-section-text {
    margin-bottom: 1.1rem;
    color: #AAB8CE;
    line-height: 1.55;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(148, 163, 184, 0.20) !important;
    border-radius: 18px !important;
    background: rgba(15, 23, 42, 0.64) !important;
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
    background: rgba(13, 30, 54, 0.56);
}

.tm-activity-time {
    color: #67E8F9;
    font-size: 0.83rem;
    font-weight: 750;
}

.tm-activity-title {
    margin-top: 0.2rem;
    color: #F8FAFC;
    font-size: 1.03rem;
    font-weight: 700;
}

.tm-activity-info {
    margin-top: 0.35rem;
    color: #B5C4D8;
    font-size: 0.9rem;
    line-height: 1.5;
}

.tm-activity-description {
    margin-top: 0.45rem;
    color: #CED9E7;
    font-size: 0.9rem;
    line-height: 1.55;
}

.tm-day-total {
    margin-top: 0.8rem;
    padding: 0.75rem 0.9rem;
    border-radius: 12px;
    background: rgba(139, 92, 246, 0.12);
    color: #E5D5FF;
    font-weight: 700;
}

.tm-map-card {
    margin-top: 1rem;
    padding: 0.5rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 18px;
    background: rgba(15, 23, 42, 0.68);
}

.tm-tip-card {
    margin: 0.65rem 0;
    padding: 1rem;
    border: 1px solid rgba(148, 163, 184, 0.17);
    border-radius: 14px;
    background: rgba(15, 23, 42, 0.64);
    color: #C8D5E5;
    line-height: 1.55;
}

.tm-expense-status {
    margin-top: 0.2rem;
    color: #AAB8CE;
    font-size: 0.78rem;
    line-height: 1.35;
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
    font-weight: 700;
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

@media (max-width: 900px) {
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.45rem;
        overflow-x: auto;
        padding: 0.48rem;
    }

    .stTabs [data-baseweb="tab"] {
        flex: 0 0 auto;
        min-height: 48px;
        padding: 0.55rem 0.85rem;
        font-size: 0.86rem;
        white-space: nowrap;
    }
}

@media (max-width: 760px) {
    .block-container {
        padding: 1.5rem 1rem 3rem;
    }

    .tm-hero {
        padding: 1.3rem;
    }

    .tm-hero-title {
        font-size: 1.85rem;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ==========================================================
# СЛОВАРИ И НАСТРОЙКИ
# ==========================================================

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
        "emoji": "💎",
        "label": "ЭКОНОМ",
        "color": "#38BDF8",
    },
    "Оптимальный": {
        "emoji": "⭐",
        "label": "ОПТИМАЛЬНЫЙ",
        "color": "#34D399",
    },
    "Премиум": {
        "emoji": "👑",
        "label": "ПРЕМИУМ",
        "color": "#A78BFA",
    },
}

# ==========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================================


def as_float(value, default=0.0):
    """Безопасно преобразует число, None или строку в float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def text_value(value, default=""):
    """Возвращает строковое значение без ошибок при None."""
    if value is None:
        return default
    return str(value)


# ==========================================================
# ШАПКА ПОЕЗДКИ
# ==========================================================

trip_title = text_value(data.get("title") or trip["title"], "Поездка")
destination = text_value(trip["destination"])
start_date_text = text_value(trip["start_date"])
end_date_text = text_value(trip["end_date"])
people = trip["people"] or 1
overview = text_value(data.get("overview"))
mood_reason = text_value(data.get("mood_reason"))

st.page_link(
    "pages/2_my_trips.py",
    label="← К моим путешествиям",
)

hero_html = f"""
<div class="tm-hero">
    <div class="tm-eyebrow">TravelMind AI · Персональный маршрут</div>
    <div class="tm-hero-title">🗺️ {escape(trip_title)}</div>
    <div class="tm-hero-meta">
        📍 {escape(destination)}<br>
        📅 {escape(start_date_text)} — {escape(end_date_text)} ·
        👥 {escape(str(people))} чел.
    </div>
"""

if overview:
    hero_html += f"""
    <div class="tm-hero-overview">{escape(overview)}</div>
    """

if mood_reason:
    hero_html += f"""
    <div class="tm-mood">🙂 {escape(mood_reason)}</div>
    """

hero_html += "</div>"

st.markdown(hero_html, unsafe_allow_html=True)

# ==========================================================
# ОСНОВНЫЕ МЕТРИКИ И КАЛЬКУЛЯЦИЯ РАСХОДОВ
# ==========================================================

expenses = db.get_expenses(trip_id)

plan_sum = sum(as_float(expense["cost_plan"]) for expense in expenses)
actual_sum = sum(as_float(expense["cost_actual"]) for expense in expenses)

total_cost = as_float(data.get("total_cost"), plan_sum)

if total_cost <= 0:
    total_cost = plan_sum

# Считаем остаток именно по строкам расходов.
# Общий бюджет поездки может быть больше этой суммы: например,
# если AI включил проживание, резерв или другие статьи.
remaining_by_items = plan_sum - actual_sum

if plan_sum <= 0:
    expense_status = "Плановые статьи расходов пока не сформированы."
    expense_status_icon = "ℹ️"

elif abs(remaining_by_items) < 0.01:
    expense_status = "Все внесённые расходы совпадают с планом."
    expense_status_icon = "✅"

elif remaining_by_items > 0:
    expense_status = (
        f"По плановым статьям ещё не внесено: "
        f"{remaining_by_items:.0f} {curr}"
    )
    expense_status_icon = "⏳"

else:
    expense_status = (
        f"Превышение плана по внесённым расходам: "
        f"{abs(remaining_by_items):.0f} {curr}"
    )
    expense_status_icon = "⚠️"

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

with metric_1:
    st.metric(
        "Общий бюджет поездки",
        f"{total_cost:.0f} {curr}",
    )

with metric_2:
    st.metric(
        "Внесено по факту",
        f"{actual_sum:.0f} {curr}",
    )
    st.caption(f"{expense_status_icon} {expense_status}")

with metric_3:
    st.metric(
        "План по строкам расходов",
        f"{plan_sum:.0f} {curr}",
    )

with metric_4:
    st.metric(
        "Дней в маршруте",
        len(data.get("days", [])),
    )

# ==========================================================
# ВКЛАДКИ
# ==========================================================

tabs = st.tabs(
    [
        "📅 Маршрут по дням",
        "🗺️ Карта поездки",
        "💳 Бюджет и расходы",
        "💡 Советы",
        "🤖 Данные AI",
    ]
)

# ==========================================================
# ВКЛАДКА 1 — МАРШРУТ ПО ДНЯМ
# ==========================================================

with tabs[0]:
    hotels = data.get("hotels") or []

    if hotels:
        st.markdown(
            '<div class="tm-section-title">🏨 Где остановиться</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="tm-section-text">
                Варианты проживания, подготовленные AI. Перед бронированием
                уточните актуальную стоимость, рейтинг и наличие номеров.
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
            tier = text_value(hotel.get("tier"), "Оптимальный")

            tier_style = TIER_STYLES.get(
                tier,
                TIER_STYLES["Оптимальный"],
            )

            hotel_name = text_value(
                hotel.get("name"),
                "Вариант проживания",
            )

            hotel_area = text_value(
                hotel.get("area"),
                "Удобный район",
            )

            hotel_why = text_value(
                hotel.get("why"),
                "Подходит для выбранного формата путешествия.",
            )

            rating = as_float(hotel.get("rating"), 0)
            rooms = hotel.get("rooms") or {}
            standard_price = as_float(rooms.get("standard"), 0)
            total_stay = standard_price * nights

            map_query = text_value(
                hotel.get(
                    "map_query",
                    f"{hotel_name} {destination}",
                )
            )

            google_maps_url = (
                "https://www.google.com/maps/search/?api=1&query="
                + quote_plus(map_query)
            )

            with hotel_columns[index]:
                # Используются нативные компоненты Streamlit.
                # HTML в карточках не применяется — теги не появятся текстом.
                with st.container(border=True):
                    st.caption(
                        f"{tier_style['emoji']} "
                        f"{tier_style['label']}"
                    )

                    st.subheader(hotel_name)
                    st.caption(f"📍 {hotel_area}")

                    if rating > 0:
                        st.write(f"⭐ Рейтинг: **{rating:.1f}/10**")
                    else:
                        st.write("⭐ Рейтинг: **уточняется**")

                    st.write(hotel_why)

                    if standard_price > 0:
                        st.info(
                            f"Стандартный номер: примерно "
                            f"**{total_stay:.0f} {curr}** "
                            f"за {nights} ноч."
                        )
                    else:
                        st.info(
                            "Стоимость номера уточняется "
                            "на сайте отеля или в сервисе бронирования."
                        )

                    st.link_button(
                        "📍 Открыть на карте",
                        google_maps_url,
                        use_container_width=True,
                    )

        st.divider()

    # Поддержка старого формата маршрута:
    # в нём проживание могло храниться в поле accommodation.
    accommodation = data.get("accommodation") or {}

    if not hotels and isinstance(accommodation, dict) and accommodation:
        accommodation_type = text_value(accommodation.get("type"))
        accommodation_area = text_value(accommodation.get("area"))
        accommodation_why = text_value(accommodation.get("why"))
        accommodation_price = as_float(
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
            with st.container(border=True):
                hotel_left, hotel_right = st.columns([3, 1])

                with hotel_left:
                    st.subheader(
                        text_value(
                            hotel.get("name"),
                            "Вариант проживания",
                        )
                    )

                    st.caption(
                        f"Категория: {text_value(hotel.get('tier'))}"
                    )

                    st.write(
                        f"📍 Район: {text_value(hotel.get('area'))}"
                    )

                    st.write(text_value(hotel.get("why")))

                with hotel_right:
                    st.metric(
                        "За ночь",
                        (
                            f"{as_float(hotel.get('price_per_night')):.0f} "
                            f"{curr}"
                        ),
                    )

    st.markdown(
        '<div class="tm-section-title">📅 План путешествия</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tm-section-text">
            План составлен с учётом последовательности активностей,
            интересов путешественника и времени в пути.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for day in data.get("days", []):
        day_number = day.get("day", "")
        day_date = text_value(day.get("date"))
        day_theme = text_value(day.get("theme"))
        day_vibe = text_value(day.get("vibe"))

        header = f"День {day_number} · {day_date}"

        if day_theme:
            header += f" — {day_theme}"

        if day_vibe:
            header += f" · {day_vibe}"

        with st.expander(header, expanded=(day_number == 1)):
            activities = day.get("activities") or []

            if not activities:
                st.info("Для этого дня пока нет активностей.")
                continue

            for activity in activities:
                activity_type = text_value(activity.get("type"))
                icon = ICONS.get(activity_type, "📍")

                time_value = text_value(activity.get("time"))
                activity_title = text_value(activity.get("title"))
                duration = text_value(activity.get("duration_min"), "?")
                cost = as_float(activity.get("cost"), 0)
                location = text_value(activity.get("location"))
                description = text_value(activity.get("description"))
                tip = text_value(activity.get("tip"))

                st.markdown(
                    f"""
                    <div class="tm-activity">
                        <div class="tm-activity-time">
                            {escape(time_value)} · {icon} ·
                            ~{cost:.0f} {escape(curr)}
                        </div>
                        <div class="tm-activity-title">
                            {escape(activity_title)}
                        </div>
                        <div class="tm-activity-info">
                            ⏱️ {escape(duration)} мин ·
                            📍 {escape(location)}
                        </div>
                        <div class="tm-activity-description">
                            {escape(description)}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if tip:
                    st.caption(f"💡 {tip}")

            day_cost = as_float(day.get("day_cost"), 0)

            st.markdown(
                f"""
                <div class="tm-day-total">
                    Итого за день: ~{day_cost:.0f} {escape(curr)}
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==========================================================
# ВКЛАДКА 2 — КАРТА ПОЕЗДКИ
# ==========================================================

with tabs[1]:
    st.markdown(
        '<div class="tm-section-title">🗺️ Карта маршрута</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tm-section-text">
            Метки обозначают рекомендованные места. Линии соединяют точки
            одного дня и показывают последовательность маршрута.
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
        st.info(
            "Для этой поездки AI не вернул координаты мест "
            "для построения карты."
        )

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
            activity_type = text_value(activity.get("type"))
            marker_color = COLORS.get(activity_type, "blue")

            popup_html = (
                f"День {escape(str(day_number))} · "
                f"{escape(text_value(activity.get('time')))}<br>"
                f"<b>{escape(text_value(activity.get('title')))}</b><br>"
                f"{escape(text_value(activity.get('location')))}"
            )

            folium.Marker(
                location=[lat, lon],
                popup=popup_html,
                tooltip=text_value(activity.get("title")),
                icon=folium.Icon(
                    color=marker_color,
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

        st.markdown(
            '<div class="tm-map-card">',
            unsafe_allow_html=True,
        )

        st_folium(
            fmap,
            use_container_width=True,
            height=520,
            returned_objects=[],
        )

        st.markdown("</div>", unsafe_allow_html=True)

        st.caption("Картографические данные: © OpenStreetMap contributors")

# ==========================================================
# ВКЛАДКА 3 — БЮДЖЕТ И РАСХОДЫ
# ==========================================================

with tabs[2]:
    st.markdown(
        '<div class="tm-section-title">💳 Бюджет и фактические расходы</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tm-section-text">
            Вносите реальные траты во время поездки. Для каждой строки
            отображается сравнение с её первоначальным планом.
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not expenses:
        st.info("Для этой поездки пока нет запланированных расходов.")

    else:
        for expense in expenses:
            expense_columns = st.columns([4, 1.35, 1.8, 0.8])

            day_number = expense["day"]
            category = expense["category"]
            expense_title = text_value(expense["title"])

            plan_cost = as_float(expense["cost_plan"], 0)
            actual_cost = as_float(expense["cost_actual"], 0)

            with expense_columns[0]:
                st.markdown(
                    f"**День {day_number} · "
                    f"{ICONS.get(category, '•')} {expense_title}**"
                )

            with expense_columns[1]:
                st.caption("План")
                st.write(f"{plan_cost:.0f} {curr}")

                item_difference = actual_cost - plan_cost

                if actual_cost == 0:
                    st.caption("Факт пока не внесён")

                elif abs(item_difference) < 0.01:
                    st.caption("✅ Совпадает с планом")

                elif item_difference < 0:
                    st.caption(
                        f"🟢 Экономия: "
                        f"{abs(item_difference):.0f} {curr}"
                    )

                else:
                    st.caption(
                        f"🔴 Превышение: "
                        f"{item_difference:.0f} {curr}"
                    )

            with expense_columns[2]:
                # Все значения передаются как float:
                # это исключает StreamlitMixedNumericTypesError.
                actual_value = st.number_input(
                    "Факт",
                    min_value=0.0,
                    max_value=10000000.0,
                    value=float(actual_cost),
                    step=10.0,
                    format="%.2f",
                    key=f"actual_{expense['id']}",
                    label_visibility="collapsed",
                )

            with expense_columns[3]:
                if st.button(
                    "💾",
                    key=f"save_{expense['id']}",
                ):
                    db.update_expense_actual(
                        expense["id"],
                        float(actual_value),
                    )
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
                "План": [
                    as_float(value)
                    for value in budget_breakdown.values()
                ],
            }
        )

        chart_data = chart_data.set_index("Категория")

        st.bar_chart(chart_data)
        st.dataframe(chart_data, use_container_width=True)

        total_by_categories = chart_data["План"].sum()

        st.caption(
            f"Сумма по категориям: {total_by_categories:.0f} {curr}"
        )

# ==========================================================
# ВКЛАДКА 4 — СОВЕТЫ
# ==========================================================

with tabs[3]:
    st.markdown(
        '<div class="tm-section-title">💡 Полезное для поездки</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tm-section-text">
            Чек-лист, полезные фразы и рекомендации, сформированные AI
            специально для выбранного направления.
        </div>
        """,
        unsafe_allow_html=True,
    )

    wow_moments = data.get("wow_moments") or []

    if wow_moments:
        st.subheader("✨ Главные впечатления")

        for moment in wow_moments:
            st.markdown(
                f'<div class="tm-tip-card">✨ {escape(text_value(moment))}</div>',
                unsafe_allow_html=True,
            )

    packing = data.get("packing") or []

    if packing:
        st.subheader("🎒 Что взять с собой")

        for index, item in enumerate(packing):
            st.checkbox(
                text_value(item),
                key=f"packing_{trip_id}_{index}",
            )

    phrases = data.get("phrases") or []

    if phrases:
        st.subheader("💬 Полезные фразы")

        for phrase in phrases:
            russian = text_value(phrase.get("ru"))
            local = text_value(phrase.get("local"))

            with st.container(border=True):
                st.markdown(f"**{russian}**")
                st.caption(local)

    tips = data.get("tips") or {}

    if tips:
        st.subheader("🧭 Советы путешественнику")

        for key, value in tips.items():
            tip_title = TIP_RU.get(key, key)

            st.markdown(
                f"""
                <div class="tm-tip-card">
                    <b>{escape(text_value(tip_title))}</b><br>
                    {escape(text_value(value))}
                </div>
                """,
                unsafe_allow_html=True,
            )

# ==========================================================
# ВКЛАДКА 5 — ДАННЫЕ AI И ЭКСПОРТ
# ==========================================================

with tabs[4]:
    st.markdown(
        '<div class="tm-section-title">🤖 Данные AI-маршрута</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tm-section-text">
            Структурированный результат работы нейросети. Его можно скачать
            для отчёта по учебному проекту или дальнейшей обработки.
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
