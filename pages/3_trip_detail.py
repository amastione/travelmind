"""Детали поездки: маршрут, карта, расходы, советы и экспорт."""
import json
from collections import defaultdict
from datetime import date
from html import escape
from urllib.parse import quote_plus

import altair as alt
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
# АВТОРИЗАЦИЯ И ЗАГРУЗКА ДАННЫХ
# ==========================================================

user_id = auth.require_auth()
trip_id = st.session_state.get("current_trip_id")

if not trip_id:
    st.warning("Поездка не выбрана. Откройте её из списка путешествий.")
    st.page_link(
        "pages/2_my_trips.py",
        label="← Перейти к моим путешествиям",
        use_container_width=True,
    )
    st.stop()

trip = db.get_trip(trip_id, user_id)

if not trip:
    st.error("Поездка не найдена или была удалена.")
    st.page_link(
        "pages/2_my_trips.py",
        label="← Перейти к моим путешествиям",
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
# СТИЛИ ПРОЕКТА
# ==========================================================

CSS = """
<style>
/* ----------------------------------------------------------
   ОСНОВА
   ---------------------------------------------------------- */

.stApp {
    background:
        radial-gradient(
            circle at 8% 8%,
            rgba(34, 211, 238, 0.13),
            transparent 29%
        ),
        radial-gradient(
            circle at 92% 88%,
            rgba(124, 92, 232, 0.16),
            transparent 34%
        ),
        linear-gradient(
            135deg,
            #060B15 0%,
            #0A1427 52%,
            #0E1325 100%
        );
    color: #F8FAFC;
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "SF Pro Display",
        "Segoe UI",
        sans-serif;
}

.block-container {
    max-width: 1220px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

#MainMenu,
footer {
    visibility: hidden;
}

/*
 ВАЖНО:
 Не добавляем span в общий селектор.
 Streamlit использует span для Material Icons.
 Иначе могут возникать артефакты вида _arrow_right.
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

/* ----------------------------------------------------------
   ШАПКА ПОЕЗДКИ
   ---------------------------------------------------------- */

.tm-hero-label {
    color: #7DEBFA;
    font-size: 0.82rem;
    font-weight: 800;
    letter-spacing: 0.1rem;
    text-transform: uppercase;
}

.tm-hero-title {
    margin: 0.42rem 0 0 !important;
    color: #FFFFFF !important;
    font-size: 2.5rem !important;
    font-weight: 820 !important;
    letter-spacing: -0.07rem;
    line-height: 1.15;
}

.tm-hero-meta {
    margin-top: 0.8rem;
    color: #D5E1F0;
    font-size: 1.04rem;
    font-weight: 600;
    line-height: 1.7;
}

.tm-overview-box {
    margin-top: 1.1rem;
    padding: 1rem 1.15rem;
    border: 1px solid rgba(125, 211, 252, 0.17);
    border-left: 3px solid #22D3EE;
    border-radius: 0 16px 16px 0;
    background: rgba(34, 211, 238, 0.06);
    color: #E0EAF5;
    font-size: 1.01rem;
    font-weight: 520;
    line-height: 1.7;
}

.tm-mood-box {
    margin-top: 0.9rem;
    color: #FDE68A;
    font-size: 0.96rem;
    font-weight: 650;
}

/* ----------------------------------------------------------
   КАРТОЧКИ И МЕТРИКИ
   ---------------------------------------------------------- */

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(148, 163, 184, 0.23) !important;
    border-radius: 22px !important;
    background: rgba(15, 23, 42, 0.70) !important;
    box-shadow:
        0 14px 32px rgba(0, 0, 0, 0.12),
        inset 0 1px 0 rgba(255, 255, 255, 0.035);
}

[data-testid="stMetric"] {
    min-height: 126px;
    padding: 1rem 1.12rem;
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 19px;
    background:
        linear-gradient(
            145deg,
            rgba(22, 33, 58, 0.78),
            rgba(10, 18, 34, 0.75)
        );
    box-shadow:
        0 13px 28px rgba(0, 0, 0, 0.13),
        inset 0 1px 0 rgba(255, 255, 255, 0.035);
}

[data-testid="stMetricLabel"] {
    color: #C7D4E6 !important;
    font-size: 0.93rem !important;
    font-weight: 680 !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 2rem !important;
    font-weight: 760 !important;
    letter-spacing: -0.05rem !important;
}

/* ----------------------------------------------------------
   ВКЛАДКИ
   ---------------------------------------------------------- */

.stTabs {
    margin-top: 2rem;
}

.stTabs [data-baseweb="tab-list"],
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    display: flex !important;
    align-items: center !important;
    gap: 0.7rem !important;
    width: 100% !important;
    min-height: 76px !important;
    overflow-x: auto !important;
    padding: 0.65rem !important;
    border: 1px solid rgba(177, 204, 235, 0.30) !important;
    border-radius: 24px !important;
    background:
        linear-gradient(
            135deg,
            rgba(29, 43, 71, 0.86),
            rgba(10, 18, 34, 0.84)
        ) !important;
    box-shadow:
        0 16px 34px rgba(0, 0, 0, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
    scrollbar-width: none;
}

.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
    display: none;
}

.stTabs [data-baseweb="tab"],
[data-testid="stTabs"] button[data-baseweb="tab"],
[data-testid="stTabs"] button[role="tab"] {
    position: relative !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex: 0 0 auto !important;
    min-height: 60px !important;
    margin: 0 !important;
    padding: 0.95rem 1.45rem !important;
    border: 1px solid rgba(228, 240, 255, 0.24) !important;
    border-radius: 19px !important;
    background: rgba(255, 255, 255, 0.085) !important;
    color: #F4F8FE !important;
    font-size: 1.24rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.025rem !important;
    line-height: 1.1 !important;
    opacity: 1 !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.09),
        0 4px 10px rgba(0, 0, 0, 0.09) !important;
    transition:
        background 200ms ease,
        border-color 200ms ease,
        color 200ms ease,
        transform 200ms ease,
        box-shadow 200ms ease !important;
}

.stTabs [data-baseweb="tab"] p,
[data-testid="stTabs"] button[data-baseweb="tab"] p,
[data-testid="stTabs"] button[role="tab"] p {
    margin: 0 !important;
    color: #F4F8FE !important;
    font-size: 1.24rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.025rem !important;
    line-height: 1.1 !important;
    white-space: nowrap !important;
}

.stTabs [data-baseweb="tab"]:hover,
[data-testid="stTabs"] button[data-baseweb="tab"]:hover,
[data-testid="stTabs"] button[role="tab"]:hover {
    z-index: 2 !important;
    border-color: rgba(165, 235, 250, 0.66) !important;
    background:
        linear-gradient(
            135deg,
            rgba(103, 232, 249, 0.20),
            rgba(139, 92, 246, 0.16)
        ) !important;
    color: #FFFFFF !important;
    transform: translateY(-1px) !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"],
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    z-index: 3 !important;
    border: 1px solid rgba(230, 250, 255, 0.92) !important;
    border-radius: 19px !important;
    background:
        radial-gradient(
            circle at 24% 0%,
            rgba(255, 255, 255, 0.24),
            transparent 40%
        ),
        linear-gradient(
            135deg,
            #0598B7 0%,
            #18CAE4 45%,
            #548AF0 74%,
            #7551DE 100%
        ) !important;
    color: #FFFFFF !important;
    font-size: 1.24rem !important;
    font-weight: 850 !important;
    box-shadow:
        0 8px 22px rgba(34, 211, 238, 0.20),
        0 5px 16px rgba(91, 74, 208, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.38) !important;
}

.stTabs [data-baseweb="tab-highlight"],
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* ----------------------------------------------------------
   ОСНОВНОЙ КОНТЕНТ
   ---------------------------------------------------------- */

.tm-section-title {
    margin-top: 1.75rem;
    margin-bottom: 0.45rem;
    color: #FFFFFF;
    font-size: 1.62rem;
    font-weight: 820;
    letter-spacing: -0.045rem;
}

.tm-section-text {
    margin-bottom: 1.2rem;
    color: #C8D5E6;
    font-size: 1.02rem;
    font-weight: 540;
    line-height: 1.68;
}

.streamlit-expanderHeader {
    border: 1px solid rgba(148, 163, 184, 0.21) !important;
    border-radius: 16px !important;
    background:
        linear-gradient(
            145deg,
            rgba(22, 33, 57, 0.78),
            rgba(11, 19, 37, 0.75)
        ) !important;
    color: #FFFFFF !important;
    font-size: 1.02rem !important;
    font-weight: 750 !important;
}

.tm-activity {
    margin: 0.85rem 0;
    padding: 1.05rem;
    border: 1px solid rgba(103, 232, 249, 0.11);
    border-left: 3px solid #22D3EE;
    border-radius: 0 16px 16px 0;
    background: rgba(13, 30, 54, 0.60);
}

.tm-activity-time {
    color: #78EAFB;
    font-size: 0.88rem;
    font-weight: 800;
}

.tm-activity-title {
    margin-top: 0.27rem;
    color: #FFFFFF;
    font-size: 1.08rem;
    font-weight: 780;
}

.tm-activity-info {
    margin-top: 0.4rem;
    color: #C7D6E8;
    font-size: 0.93rem;
    font-weight: 580;
    line-height: 1.55;
}

.tm-activity-description {
    margin-top: 0.46rem;
    color: #DEE8F2;
    font-size: 0.93rem;
    font-weight: 520;
    line-height: 1.6;
}

.tm-day-total {
    margin-top: 0.9rem;
    padding: 0.82rem 0.98rem;
    border: 1px solid rgba(167, 139, 250, 0.18);
    border-radius: 14px;
    background: rgba(139, 92, 246, 0.14);
    color: #F0EAFF;
    font-size: 0.96rem;
    font-weight: 750;
}

.tm-map-card {
    margin-top: 1rem;
    padding: 0.5rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 20px;
    background: rgba(15, 23, 42, 0.68);
}

.tm-tip-card {
    margin: 0.7rem 0;
    padding: 1.05rem;
    border: 1px solid rgba(148, 163, 184, 0.19);
    border-radius: 16px;
    background: rgba(15, 23, 42, 0.68);
    color: #D8E3EF;
    font-size: 0.96rem;
    font-weight: 540;
    line-height: 1.62;
}

/* ----------------------------------------------------------
   КНОПКИ И ПОЛЯ ВВОДА
   ---------------------------------------------------------- */

.stButton > button,
.stLinkButton > a,
.stDownloadButton > button {
    min-height: 46px;
    border: 0 !important;
    border-radius: 14px !important;
    background: linear-gradient(
        135deg,
        #06B6D4 0%,
        #22D3EE 47%,
        #8B5CF6 100%
    ) !important;
    color: #FFFFFF !important;
    font-size: 0.97rem;
    font-weight: 750;
    box-shadow:
        0 10px 23px rgba(34, 211, 238, 0.17),
        inset 0 1px 0 rgba(255, 255, 255, 0.20);
}

.stButton > button:hover,
.stLinkButton > a:hover,
.stDownloadButton > button:hover {
    transform: translateY(-1px);
    filter: brightness(1.07);
}

.stNumberInput input {
    border: 1px solid rgba(148, 163, 184, 0.34) !important;
    border-radius: 11px !important;
    background: rgba(7, 11, 20, 0.70) !important;
    color: #FFFFFF !important;
    font-weight: 650 !important;
}

/* ----------------------------------------------------------
   ГРАФИК И ТАБЛИЦА БЮДЖЕТА
   ---------------------------------------------------------- */

[data-testid="stDataFrame"] {
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 18px;
    overflow: hidden;
    background: rgba(15, 23, 42, 0.66);
}

[data-testid="stDataFrame"] [role="grid"] {
    background: rgba(15, 23, 42, 0.66) !important;
    color: #E8F1FA !important;
}

[data-testid="stDataFrame"] [role="columnheader"] {
    background: rgba(34, 211, 238, 0.09) !important;
    color: #F8FAFC !important;
    font-weight: 750 !important;
}

[data-testid="stDataFrame"] [role="gridcell"] {
    background: rgba(15, 23, 42, 0.60) !important;
    color: #D9E5F3 !important;
    border-color: rgba(148, 163, 184, 0.13) !important;
}

/* ----------------------------------------------------------
   МОБИЛЬНАЯ АДАПТАЦИЯ
   ---------------------------------------------------------- */

@media (max-width: 900px) {
    .stTabs [data-baseweb="tab-list"],
    [data-testid="stTabs"] [data-baseweb="tab-list"] {
        gap: 0.5rem !important;
        min-height: 71px !important;
        padding: 0.55rem !important;
        border-radius: 21px !important;
    }

    .stTabs [data-baseweb="tab"],
    [data-testid="stTabs"] button[data-baseweb="tab"],
    [data-testid="stTabs"] button[role="tab"] {
        min-height: 57px !important;
        padding: 0.88rem 1.18rem !important;
        font-size: 1.12rem !important;
        font-weight: 800 !important;
    }

    .stTabs [data-baseweb="tab"] p,
    [data-testid="stTabs"] button[data-baseweb="tab"] p,
    [data-testid="stTabs"] button[role="tab"] p {
        font-size: 1.12rem !important;
        font-weight: 800 !important;
    }
}

@media (max-width: 760px) {
    .block-container {
        padding: 1.5rem 1rem 3rem;
    }

    .tm-hero-title {
        font-size: 1.9rem !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.65rem !important;
    }

    .stTabs {
        margin-top: 1.55rem;
    }

    .stTabs [data-baseweb="tab"],
    [data-testid="stTabs"] button[data-baseweb="tab"],
    [data-testid="stTabs"] button[role="tab"] {
        min-height: 55px !important;
        padding: 0.84rem 1.08rem !important;
        font-size: 1.05rem !important;
    }

    .stTabs [data-baseweb="tab"] p,
    [data-testid="stTabs"] button[data-baseweb="tab"] p,
    [data-testid="stTabs"] button[role="tab"] p {
        font-size: 1.05rem !important;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ==========================================================
# СЛОВАРИ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
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
    "Эконом": {"emoji": "💎", "label": "ЭКОНОМ"},
    "Оптимальный": {"emoji": "⭐", "label": "ОПТИМАЛЬНЫЙ"},
    "Премиум": {"emoji": "👑", "label": "ПРЕМИУМ"},
}


def as_float(value, default=0.0):
    """Безопасно преобразует значение в число."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def text_value(value, default=""):
    """Безопасно преобразует значение в строку."""
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

with st.container(border=True):
    st.markdown(
        '<div class="tm-hero-label">TravelMind AI · Персональный маршрут</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'<h1 class="tm-hero-title">🗺️ {escape(trip_title)}</h1>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="tm-hero-meta">'
            f'📍 {escape(destination)}<br>'
            f'📅 {escape(start_date_text)} — {escape(end_date_text)} · '
            f'👥 {people} чел.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    if overview:
        st.markdown(
            f'<div class="tm-overview-box">{escape(overview)}</div>',
            unsafe_allow_html=True,
        )

    if mood_reason:
        st.markdown(
            f'<div class="tm-mood-box">🙂 {escape(mood_reason)}</div>',
            unsafe_allow_html=True,
        )

# ==========================================================
# МЕТРИКИ
# ==========================================================

expenses = db.get_expenses(trip_id)

plan_sum = sum(as_float(expense["cost_plan"]) for expense in expenses)
actual_sum = sum(as_float(expense["cost_actual"]) for expense in expenses)

total_cost = as_float(data.get("total_cost"), plan_sum)

if total_cost <= 0:
    total_cost = plan_sum

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
    st.metric("Общий бюджет поездки", f"{total_cost:.0f} {curr}")

with metric_2:
    st.metric("Внесено по факту", f"{actual_sum:.0f} {curr}")
    st.caption(f"{expense_status_icon} {expense_status}")

with metric_3:
    st.metric("План по строкам расходов", f"{plan_sum:.0f} {curr}")

with metric_4:
    st.metric("Дней в маршруте", len(data.get("days", [])))

# ==========================================================
# ВКЛАДКИ
# ==========================================================

tab_route, tab_map, tab_budget, tab_tips, tab_ai = st.tabs(
    [
        "▦  Маршрут по дням",
        "⌖  Карта поездки",
        "◫  Бюджет и расходы",
        "✦  Советы",
        "⌘  Данные AI",
    ]
)

# ==========================================================
# ВКЛАДКА 1 — МАРШРУТ
# ==========================================================

with tab_route:
    hotels = data.get("hotels") or []

    if hotels:
        st.markdown(
            '<div class="tm-section-title">🏨 Где остановиться</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="tm-section-text">
                Варианты проживания подготовлены AI. Перед бронированием
                обязательно уточните актуальную стоимость и наличие номеров.
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
            tier_style = TIER_STYLES.get(tier, TIER_STYLES["Оптимальный"])

            hotel_name = text_value(hotel.get("name"), "Вариант проживания")
            hotel_area = text_value(hotel.get("area"), "Удобный район")
            hotel_why = text_value(
                hotel.get("why"),
                "Подходит для выбранного формата путешествия.",
            )

            rating = as_float(hotel.get("rating"), 0)
            rooms = hotel.get("rooms") or {}
            standard_price = as_float(rooms.get("standard"), 0)
            total_stay = standard_price * nights

            map_query = text_value(
                hotel.get("map_query", f"{hotel_name} {destination}")
            )

            google_maps_url = (
                "https://www.google.com/maps/search/?api=1&query="
                + quote_plus(map_query)
            )

            with hotel_columns[index]:
                with st.container(border=True):
                    st.caption(f"{tier_style['emoji']} {tier_style['label']}")
                    st.subheader(hotel_name)
                    st.caption(f"📍 {hotel_area}")

                    if rating > 0:
                        st.write(f"⭐ Рейтинг: **{rating:.1f}/10**")
                    else:
                        st.write("⭐ Рейтинг уточняется")

                    st.write(hotel_why)

                    if standard_price > 0:
                        st.info(
                            f"Стандартный номер: примерно "
                            f"**{total_stay:.0f} {curr}** "
                            f"за {nights} ноч."
                        )
                    else:
                        st.info(
                            "Стоимость уточняется на сайте отеля "
                            "или в сервисе бронирования."
                        )

                    st.link_button(
                        "⌖ Открыть на карте",
                        google_maps_url,
                        use_container_width=True,
                    )

        st.divider()

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
            f"🏨 Проживание: {accommodation_type}, район "
            f"{accommodation_area} · примерно "
            f"{accommodation_price:.0f} {curr}/ночь. "
            f"{accommodation_why}"
        )

    st.markdown(
        '<div class="tm-section-title">📅 План путешествия</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tm-section-text">
            План составлен с учётом интересов, логистики и темпа поездки.
        </div>
        """,
        unsafe_allow_html=True,
    )

    for day in data.get("days", []):
        day_number = day.get("day", "")
        day_date = text_value(day.get("date"))
        day_theme = text_value(day.get("theme"))
        day_vibe = text_value(day.get("vibe"))

        day_header = f"День {day_number} · {day_date}"

        if day_theme:
            day_header += f" — {day_theme}"

        if day_vibe:
            day_header += f" · {day_vibe}"

        with st.expander(day_header, expanded=(day_number == 1)):
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

                activity_html = (
                    '<div class="tm-activity">'
                    '<div class="tm-activity-time">'
                    f'{escape(time_value)} · {icon} · '
                    f'~{cost:.0f} {escape(curr)}'
                    '</div>'
                    '<div class="tm-activity-title">'
                    f'{escape(activity_title)}'
                    '</div>'
                    '<div class="tm-activity-info">'
                    f'⏱️ {escape(duration)} мин · '
                    f'⌖ {escape(location)}'
                    '</div>'
                    '<div class="tm-activity-description">'
                    f'{escape(description)}'
                    '</div>'
                    '</div>'
                )

                st.markdown(activity_html, unsafe_allow_html=True)

                if tip:
                    st.caption(f"✦ {tip}")

            day_cost = as_float(day.get("day_cost"), 0)

            st.markdown(
                (
                    '<div class="tm-day-total">'
                    f'Итого за день: ~{day_cost:.0f} {escape(curr)}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

# ==========================================================
# ВКЛАДКА 2 — КАРТА
# ==========================================================

with tab_map:
    st.markdown(
        '<div class="tm-section-title">⌖ Карта маршрута</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tm-section-text">
            Метки показывают рекомендованные места, а линии соединяют точки
            одного дня в порядке следования маршрута.
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
                points.append((lat, lon, activity, day.get("day")))

    if not points:
        st.info(
            "Для этой поездки AI не вернул координаты "
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

        st.markdown('<div class="tm-map-card">', unsafe_allow_html=True)

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

with tab_budget:
    st.markdown(
        '<div class="tm-section-title">◫ Бюджет и фактические расходы</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="tm-section-text">
            Вносите реальные траты во время поездки. Для каждой позиции
            отображается сравнение с первоначальным планом.
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

                difference = actual_cost - plan_cost

                if actual_cost == 0:
                    st.caption("Факт пока не внесён")
                elif abs(difference) < 0.01:
                    st.caption("✅ Совпадает с планом")
                elif difference < 0:
                    st.caption(f"🟢 Экономия: {abs(difference):.0f} {curr}")
                else:
                    st.caption(f"🔴 Превышение: {difference:.0f} {curr}")

            with expense_columns[2]:
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
                if st.button("💾", key=f"save_{expense['id']}"):
                    db.update_expense_actual(
                        expense["id"],
                        float(actual_value),
                    )
                    st.toast("Расход сохранён")
                    st.rerun()

            st.divider()

    # ------------------------------------------------------
    # КАСТОМНЫЙ ГРАФИК БЮДЖЕТА
    # ------------------------------------------------------

    budget_breakdown = data.get("budget_breakdown") or {}

    if budget_breakdown:
        st.markdown(
            '<div class="tm-section-title">◫ Структура планового бюджета</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="tm-section-text">
                Распределение ориентировочного бюджета по основным категориям поездки.
            </div>
            """,
            unsafe_allow_html=True,
        )

        budget_rows = []

        for key, value in budget_breakdown.items():
            category_name = BUDGET_RU.get(key, key)
            amount = as_float(value)

            if amount > 0:
                budget_rows.append(
                    {
                        "Категория": category_name,
                        "План": amount,
                        "Сумма": (
                            f"{amount:,.0f} {curr}"
                        ).replace(",", " "),
                    }
                )

        if budget_rows:
            chart_data = pd.DataFrame(budget_rows)

            total_budget_breakdown = chart_data["План"].sum()

            chart_data["Доля"] = (
                chart_data["План"] / total_budget_breakdown * 100
            ).round(1)

            chart_data["Подпись"] = chart_data["План"].apply(
                lambda value: f"{value:,.0f}".replace(",", " ")
            )

            palette = [
                "#22D3EE",
                "#38BDF8",
                "#818CF8",
                "#A78BFA",
                "#C084FC",
            ]

            base_chart = (
                alt.Chart(chart_data)
                .mark_bar(
                    cornerRadiusTopLeft=12,
                    cornerRadiusTopRight=12,
                    size=72,
                )
                .encode(
                    x=alt.X(
                        "Категория:N",
                        sort="-y",
                        axis=alt.Axis(
                            title=None,
                            labelColor="#D8E5F5",
                            labelFontSize=14,
                            labelFontWeight=650,
                            labelAngle=0,
                            labelPadding=14,
                            domain=False,
                            ticks=False,
                        ),
                    ),
                    y=alt.Y(
                        "План:Q",
                        axis=alt.Axis(
                            title=None,
                            labelColor="#B9C9DC",
                            labelFontSize=13,
                            labelPadding=10,
                            domain=False,
                            ticks=False,
                            grid=True,
                            gridColor="#314158",
                            gridOpacity=0.6,
                        ),
                    ),
                    color=alt.Color(
                        "Категория:N",
                        scale=alt.Scale(range=palette),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip(
                            "Категория:N",
                            title="Категория",
                        ),
                        alt.Tooltip(
                            "Сумма:N",
                            title="План",
                        ),
                        alt.Tooltip(
                            "Доля:Q",
                            title="Доля бюджета",
                            format=".1f",
                        ),
                    ],
                )
                .properties(
                    height=330,
                    padding={
                        "top": 25,
                        "right": 16,
                        "bottom": 8,
                        "left": 6,
                    },
                )
            )

            value_labels = (
                alt.Chart(chart_data)
                .mark_text(
                    align="center",
                    baseline="bottom",
                    dy=-9,
                    color="#F8FAFC",
                    font="Inter",
                    fontSize=13,
                    fontWeight=700,
                )
                .encode(
                    x=alt.X(
                        "Категория:N",
                        sort="-y",
                    ),
                    y=alt.Y("План:Q"),
                    text=alt.Text("Подпись:N"),
                )
            )

            final_chart = (
                base_chart + value_labels
            ).configure_view(
                strokeOpacity=0,
                fill="transparent",
            ).configure_axis(
                labelFont="Inter",
                titleFont="Inter",
            ).configure(
                background="transparent",
            )

            with st.container(border=True):
                st.altair_chart(
                    final_chart,
                    use_container_width=True,
                    theme=None,
                )

                formatted_total = (
                    f"{total_budget_breakdown:,.0f} {curr}"
                ).replace(",", " ")

                st.caption(
                    f"Общий плановый бюджет: **{formatted_total}**"
                )

            table_rows = []

            for item in chart_data.to_dict("records"):
                table_rows.append(
                    {
                        "Категория": item["Категория"],
                        "План": item["Сумма"],
                        "Доля бюджета": f"{item['Доля']:.1f}%",
                    }
                )

            budget_table = pd.DataFrame(table_rows)

            st.markdown(
                '<div class="tm-section-title">Детализация бюджета</div>',
                unsafe_allow_html=True,
            )

            st.dataframe(
                budget_table,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Категория": st.column_config.TextColumn(
                        "Категория",
                        width="large",
                    ),
                    "План": st.column_config.TextColumn(
                        "План",
                        width="medium",
                    ),
                    "Доля бюджета": st.column_config.TextColumn(
                        "Доля бюджета",
                        width="medium",
                    ),
                },
            )
        else:
            st.info("В структуре бюджета нет положительных значений.")

# ==========================================================
# ВКЛАДКА 4 — СОВЕТЫ
# ==========================================================

with tab_tips:
    st.markdown(
        '<div class="tm-section-title">✦ Полезное для поездки</div>',
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
        st.subheader("✦ Главные впечатления")

        for moment in wow_moments:
            st.markdown(
                (
                    '<div class="tm-tip-card">'
                    f'✦ {escape(text_value(moment))}'
                    '</div>'
                ),
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
                (
                    '<div class="tm-tip-card">'
                    f'<b>{escape(text_value(tip_title))}</b><br>'
                    f'{escape(text_value(value))}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

# ==========================================================
# ВКЛАДКА 5 — ДАННЫЕ AI И ЭКСПОРТ
# ==========================================================

with tab_ai:
    st.markdown(
        '<div class="tm-section-title">⌘ Данные AI-маршрута</div>',
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
    json_content = json.dumps(data, ensure_ascii=False, indent=2)

    with download_markdown:
        st.download_button(
            label="⬇ Скачать маршрут в Markdown",
            data=markdown_content,
            file_name=f"travelmind_trip_{trip_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with download_json:
        st.download_button(
            label="⬇ Скачать маршрут в JSON",
            data=json_content,
            file_name=f"travelmind_trip_{trip_id}.json",
            mime="application/json",
            use_container_width=True,
        )
