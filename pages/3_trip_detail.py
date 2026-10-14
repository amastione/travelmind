"""Детали поездки: маршрут, карта, расходы, советы и экспорт."""
import json
from collections import defaultdict
from datetime import date, datetime
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
    auth.remember_trip(trip_id)
try:
    data = json.loads(trip["data"])
except (json.JSONDecodeError, TypeError):
    st.error("Не удалось прочитать данные маршрута.")
    st.stop()

curr = trip["currency"] or "RUB"

# ==========================================================
# СТИЛИ
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
 Важно: span не добавляем сюда.
 Streamlit использует span для системных Material Icons.
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
    font-weight: 800 !important;
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
}

[data-testid="stMetricLabel"] {
    color: #C7D4E6 !important;
    font-size: 0.93rem !important;
    font-weight: 700 !important;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-size: 2rem !important;
    font-weight: 750 !important;
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
    white-space: nowrap !important;
}

.stTabs [data-baseweb="tab"] p,
[data-testid="stTabs"] button[data-baseweb="tab"] p,
[data-testid="stTabs"] button[role="tab"] p {
    margin: 0 !important;
    color: #F4F8FE !important;
    font-size: 1.24rem !important;
    font-weight: 800 !important;
    white-space: nowrap !important;
}

.stTabs [data-baseweb="tab"]:hover,
[data-testid="stTabs"] button[data-baseweb="tab"]:hover,
[data-testid="stTabs"] button[role="tab"]:hover {
    border-color: rgba(165, 235, 250, 0.66) !important;
    background:
        linear-gradient(
            135deg,
            rgba(103, 232, 249, 0.20),
            rgba(139, 92, 246, 0.16)
        ) !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"],
.stTabs [data-baseweb="tab"][aria-selected="true"]:hover,
.stTabs [data-baseweb="tab"][aria-selected="true"]:focus,
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"],
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"]:hover,
[data-testid="stTabs"] button[data-baseweb="tab"][aria-selected="true"]:focus,
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    border: 1px solid rgba(230, 250, 255, 0.92) !important;
    border-radius: 19px !important;
    outline: none !important;
    background:
        linear-gradient(
            135deg,
            #0598B7 0%,
            #18CAE4 45%,
            #548AF0 74%,
            #7551DE 100%
        ) !important;
    color: #FFFFFF !important;
    box-shadow:
        0 8px 22px rgba(34, 211, 238, 0.22),
        inset 0 1px 0 rgba(255, 255, 255, 0.28) !important;
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
    font-weight: 800;
    letter-spacing: -0.045rem;
}

.tm-section-text {
    margin-bottom: 1.2rem;
    color: #C8D5E6;
    font-size: 1.02rem;
    line-height: 1.68;
}

/* ----------------------------------------------------------
   РАСКРЫВАЕМЫЕ ДНИ МАРШРУТА — ИСПРАВЛЕНИЕ БЕЛОГО ФОНА
   ---------------------------------------------------------- */

/* Карточка раскрываемого дня */
details[data-testid="stExpander"] {
    overflow: hidden !important;
    margin-bottom: 0.9rem !important;
    border: 1px solid rgba(103, 232, 249, 0.22) !important;
    border-radius: 18px !important;
    background: rgba(10, 22, 42, 0.78) !important;
    box-shadow:
        0 12px 28px rgba(0, 0, 0, 0.12),
        inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
}

/* Заголовок дня — закрытое состояние */
details[data-testid="stExpander"] > summary {
    min-height: 64px !important;
    padding: 1.05rem 1.2rem !important;
    border: 0 !important;
    border-radius: 17px !important;
    background:
        linear-gradient(
            135deg,
            rgba(29, 49, 77, 0.98),
            rgba(14, 25, 47, 0.98)
        ) !important;
    color: #F8FAFC !important;
    cursor: pointer !important;
}

/*
 Текст заголовка. Это локальный span только внутри раскрывающегося
 компонента, поэтому системные Material Icons не ломаются.
*/
details[data-testid="stExpander"] > summary p,
details[data-testid="stExpander"] > summary div,
details[data-testid="stExpander"] > summary span {
    color: #F8FAFC !important;
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif !important;
    font-size: 1.04rem !important;
    font-weight: 750 !important;
}

/* Заголовок открытого дня */
details[data-testid="stExpander"][open] > summary {
    border-bottom: 1px solid rgba(103, 232, 249, 0.22) !important;
    border-radius: 17px 17px 0 0 !important;
    background:
        linear-gradient(
            135deg,
            rgba(8, 142, 175, 0.50),
            rgba(75, 69, 177, 0.42)
        ) !important;
    color: #FFFFFF !important;
}

/* Текст заголовка открытого дня */
details[data-testid="stExpander"][open] > summary p,
details[data-testid="stExpander"][open] > summary div,
details[data-testid="stExpander"][open] > summary span {
    color: #FFFFFF !important;
}

/* Hover */
details[data-testid="stExpander"] > summary:hover {
    background:
        linear-gradient(
            135deg,
            rgba(19, 104, 137, 0.62),
            rgba(75, 62, 153, 0.50)
        ) !important;
}

/* Стрелка раскрытия */
details[data-testid="stExpander"] > summary svg {
    fill: #7DEBFA !important;
    color: #7DEBFA !important;
}

/* Контент раскрытого дня */
details[data-testid="stExpander"] [data-testid="stExpanderDetails"],
details[data-testid="stExpander"] > div {
    background: rgba(8, 18, 35, 0.70) !important;
}

/* Дополнительный селектор для некоторых версий Streamlit */
[data-testid="stExpander"] summary {
    background-color: transparent !important;
}

/* ----------------------------------------------------------
   АКТИВНОСТИ МАРШРУТА
   ---------------------------------------------------------- */

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
    font-weight: 750;
}

.tm-activity-info {
    margin-top: 0.4rem;
    color: #C7D6E8;
    font-size: 0.93rem;
    line-height: 1.55;
}

.tm-activity-description {
    margin-top: 0.46rem;
    color: #DEE8F2;
    font-size: 0.93rem;
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

.tm-tip-card {
    margin: 0.7rem 0;
    padding: 1.05rem;
    border: 1px solid rgba(148, 163, 184, 0.19);
    border-radius: 16px;
    background: rgba(15, 23, 42, 0.68);
    color: #D8E3EF;
    font-size: 0.96rem;
    line-height: 1.62;
}

/* ----------------------------------------------------------
   ДЕТАЛИЗАЦИЯ БЮДЖЕТА
   ---------------------------------------------------------- */

.tm-budget-card {
    display: grid;
    grid-template-columns: minmax(160px, 1.4fr) minmax(160px, 3fr) auto;
    align-items: center;
    gap: 1rem;
    margin: 0.7rem 0;
    padding: 1rem 1.1rem;
    border: 1px solid rgba(148, 163, 184, 0.22);
    border-radius: 18px;
    background:
        linear-gradient(
            135deg,
            rgba(27, 42, 68, 0.78),
            rgba(11, 20, 39, 0.74)
        );
}

.tm-budget-category {
    display: flex;
    align-items: center;
    gap: 0.72rem;
    min-width: 0;
    color: #F2F7FC;
    font-size: 1rem;
    font-weight: 750;
}

.tm-budget-dot {
    width: 12px;
    min-width: 12px;
    height: 12px;
    border-radius: 50%;
    box-shadow: 0 0 12px currentColor;
}

.tm-budget-progress {
    width: 100%;
    height: 10px;
    overflow: hidden;
    border: 1px solid rgba(226, 232, 240, 0.10);
    border-radius: 999px;
    background: rgba(148, 163, 184, 0.15);
}

.tm-budget-progress-value {
    height: 100%;
    min-width: 6px;
    border-radius: 999px;
}

.tm-budget-percent {
    margin-top: 0.42rem;
    color: #AABDD3;
    font-size: 0.78rem;
    font-weight: 650;
}

.tm-budget-amount {
    color: #FFFFFF;
    font-size: 1.03rem;
    font-weight: 800;
    text-align: right;
    white-space: nowrap;
}

/* ----------------------------------------------------------
   КНОПКИ И ПОЛЯ
   ---------------------------------------------------------- */

.stButton > button,
.stLinkButton > a,
.stDownloadButton > button {
    min-height: 46px;
    border: 0 !important;
    border-radius: 14px !important;
    background:
        linear-gradient(
            135deg,
            #06B6D4 0%,
            #22D3EE 47%,
            #8B5CF6 100%
        ) !important;
    color: #FFFFFF !important;
    font-size: 0.97rem;
    font-weight: 750;
}

.stNumberInput input {
    border: 1px solid rgba(148, 163, 184, 0.34) !important;
    border-radius: 11px !important;
    background: rgba(7, 11, 20, 0.70) !important;
    color: #FFFFFF !important;
    font-weight: 650 !important;
}

@media (max-width: 760px) {
    .block-container {
        padding: 1.5rem 1rem 3rem;
    }

    .tm-hero-title {
        font-size: 1.9rem !important;
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

    .tm-budget-card {
        grid-template-columns: 1fr;
        gap: 0.72rem;
    }

    .tm-budget-amount {
        text-align: left;
    }
}
/* ----------------------------------------------------------
   ЯРКИЕ КНОПКИ НАВИГАЦИИ STREAMLIT
   Главное меню / К моим путешествиям
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

/* Текст внутри яркой page_link-кнопки */
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] p,
[data-testid="stPageLink-NavLink"] p {
    margin: 0 !important;
    color: #FFFFFF !important;
    font-size: 0.96rem !important;
    font-weight: 800 !important;
}

/* Hover-состояние */
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:hover,
[data-testid="stPageLink-NavLink"]:hover {
    transform: translateY(-2px) !important;
    filter: brightness(1.09) saturate(1.06) !important;
    box-shadow:
        0 16px 30px rgba(34, 211, 238, 0.29),
        0 12px 25px rgba(139, 92, 246, 0.21),
        inset 0 1px 0 rgba(255, 255, 255, 0.34) !important;
}

/* Фокус с клавиатуры */
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:focus-visible,
[data-testid="stPageLink-NavLink"]:focus-visible {
    outline: 3px solid rgba(125, 235, 250, 0.88) !important;
    outline-offset: 3px !important;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

auth.render_main_menu_button()

# ==========================================================
# СЛОВАРИ И ФУНКЦИИ
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

BUDGET_COLORS = [
    "#22D3EE",
    "#38BDF8",
    "#818CF8",
    "#A78BFA",
    "#C084FC",
]


def as_float(value, default=0.0):
    """Безопасно приводит значение к float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def text_value(value, default=""):
    """Безопасно приводит значение к строке."""
    if value is None:
        return default
    return str(value)


def format_money(value, currency):
    """Форматирует денежную сумму."""
    return f"{as_float(value):,.0f} {currency}".replace(",", " ")
def format_date_ru(value) -> str:
    """
    Преобразует YYYY-MM-DD в DD/MM/YYYY для интерфейса.
    Данные AI и БД при этом продолжают храниться в ISO-формате.
    """
    if not value:
        return ""

    text = str(value)

    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return text


# ==========================================================
# ШАПКА ПОЕЗДКИ
# ==========================================================

trip_title = text_value(data.get("title") or trip["title"], "Поездка")
destination = text_value(trip["destination"])
start_date_text = format_date_ru(trip["start_date"])
end_date_text = format_date_ru(trip["end_date"])
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

plan_sum = sum(as_float(item["cost_plan"]) for item in expenses)
actual_sum = sum(as_float(item["cost_actual"]) for item in expenses)
total_cost = as_float(data.get("total_cost"), plan_sum)

if total_cost <= 0:
    total_cost = plan_sum

remaining = plan_sum - actual_sum

if plan_sum <= 0:
    status_text = "Плановые статьи расходов пока не сформированы."
    status_icon = "ℹ️"
elif abs(remaining) < 0.01:
    status_text = "Все внесённые расходы совпадают с планом."
    status_icon = "✅"
elif remaining > 0:
    status_text = (
        f"По плановым статьям ещё не внесено: {remaining:.0f} {curr}"
    )
    status_icon = "⏳"
else:
    status_text = f"Превышение плана: {abs(remaining):.0f} {curr}"
    status_icon = "⚠️"

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

with metric_1:
    st.metric("Общий бюджет поездки", format_money(total_cost, curr))

with metric_2:
    st.metric("Внесено по факту", format_money(actual_sum, curr))
    st.caption(f"{status_icon} {status_text}")

with metric_3:
    st.metric("План по строкам расходов", format_money(plan_sum, curr))

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
            (
                '<div class="tm-section-text">'
                'Варианты проживания подготовлены AI. Перед бронированием '
                'уточните актуальную стоимость и наличие номеров.'
                '</div>'
            ),
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
            standard_price = as_float(
                (hotel.get("rooms") or {}).get("standard"),
                0,
            )
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
                            f"Примерно **{format_money(total_stay, curr)}** "
                            f"за {nights} ноч."
                        )
                    else:
                        st.info("Стоимость уточняется на сайте отеля.")

                    st.link_button(
                        "⌖ Открыть на карте",
                        google_maps_url,
                        use_container_width=True,
                    )

        st.divider()

    st.markdown(
        '<div class="tm-section-title">📅 План путешествия</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="tm-section-text">'
            'План составлен с учётом интересов, логистики и темпа поездки.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    for day in data.get("days", []):
        day_number = day.get("day", "")
        day_date = format_date_ru(day.get("date"))
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
                title = text_value(activity.get("title"))
                duration = text_value(activity.get("duration_min"), "?")
                cost = as_float(activity.get("cost"), 0)
                location = text_value(activity.get("location"))
                description = text_value(activity.get("description"))
                tip = text_value(activity.get("tip"))

                st.markdown(
                    (
                        '<div class="tm-activity">'
                        '<div class="tm-activity-time">'
                        f'{escape(time_value)} · {icon} · '
                        f'~{format_money(cost, curr)}'
                        '</div>'
                        '<div class="tm-activity-title">'
                        f'{escape(title)}'
                        '</div>'
                        '<div class="tm-activity-info">'
                        f'⏱️ {escape(duration)} мин · '
                        f'⌖ {escape(location)}'
                        '</div>'
                        '<div class="tm-activity-description">'
                        f'{escape(description)}'
                        '</div>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                if tip:
                    st.caption(f"✦ {tip}")

            day_cost = as_float(day.get("day_cost"), 0)

            st.markdown(
                (
                    '<div class="tm-day-total">'
                    f'Итого за день: ~{format_money(day_cost, curr)}'
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
        (
            '<div class="tm-section-text">'
            'Метки показывают рекомендованные места, а линии соединяют '
            'точки одного дня в порядке следования маршрута.'
            '</div>'
        ),
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
        st.info("Для этой поездки AI не вернул координаты для карты.")
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
            attribution_control=False,
        )

        points_by_day = defaultdict(list)

        for lat, lon, activity, day_number in points:
            activity_type = text_value(activity.get("type"))
            points_by_day[day_number].append([lat, lon])

            popup_html = (
                f"День {escape(str(day_number))}<br>"
                f"<b>{escape(text_value(activity.get('title')))}</b><br>"
                f"{escape(text_value(activity.get('location')))}"
            )

            folium.Marker(
                location=[lat, lon],
                popup=popup_html,
                tooltip=text_value(activity.get("title")),
                icon=folium.Icon(
                    color=COLORS.get(activity_type, "blue"),
                    icon="info-sign",
                ),
            ).add_to(fmap)

        for route_points in points_by_day.values():
            if len(route_points) > 1:
                folium.PolyLine(
                    route_points,
                    weight=3,
                    opacity=0.75,
                    color="#22D3EE",
                ).add_to(fmap)

        with st.container(border=True):
            st_folium(
                fmap,
                use_container_width=True,
                height=520,
                returned_objects=[],
            )

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
        (
            '<div class="tm-section-text">'
            'Вносите реальные траты во время поездки. Для каждой позиции '
            'отображается сравнение с первоначальным планом.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    if not expenses:
        st.info("Для этой поездки пока нет запланированных расходов.")

    for expense in expenses:
        columns = st.columns([4, 1.35, 1.8, 0.8])

        day_number = expense["day"]
        category = expense["category"]
        title = text_value(expense["title"])
        plan_cost = as_float(expense["cost_plan"])
        actual_cost = as_float(expense["cost_actual"])

        with columns[0]:
            st.markdown(
                f"**День {day_number} · "
                f"{ICONS.get(category, '•')} {title}**"
            )

        with columns[1]:
            st.caption("План")
            st.write(format_money(plan_cost, curr))

            difference = actual_cost - plan_cost

            if actual_cost == 0:
                st.caption("Факт пока не внесён")
            elif abs(difference) < 0.01:
                st.caption("✅ Совпадает с планом")
            elif difference < 0:
                st.caption(
                    f"🟢 Экономия: {format_money(abs(difference), curr)}"
                )
            else:
                st.caption(
                    f"🔴 Превышение: {format_money(difference, curr)}"
                )

        with columns[2]:
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

        with columns[3]:
            if st.button("💾", key=f"save_{expense['id']}"):
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
            '<div class="tm-section-title">◫ Структура планового бюджета</div>',
            unsafe_allow_html=True,
        )

        budget_rows = []

        for key, value in budget_breakdown.items():
            amount = as_float(value)

            if amount > 0:
                budget_rows.append(
                    {
                        "Категория": BUDGET_RU.get(key, key),
                        "План": amount,
                        "Сумма": format_money(amount, curr),
                    }
                )

        if budget_rows:
            chart_data = pd.DataFrame(budget_rows)
            total_breakdown = chart_data["План"].sum()

            chart_data["Доля"] = (
                chart_data["План"] / total_breakdown * 100
            ).round(1)

            final_chart = (
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
                            gridOpacity=0.60,
                        ),
                    ),
                    color=alt.Color(
                        "Категория:N",
                        scale=alt.Scale(range=BUDGET_COLORS),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("Категория:N", title="Категория"),
                        alt.Tooltip("Сумма:N", title="План"),
                        alt.Tooltip(
                            "Доля:Q",
                            title="Доля бюджета, %",
                            format=".1f",
                        ),
                    ],
                )
                .properties(height=330)
                .configure_view(
                    strokeOpacity=0,
                    fill="transparent",
                )
                .configure(background="transparent")
            )

            with st.container(border=True):
                st.altair_chart(
                    final_chart,
                    use_container_width=True,
                    theme=None,
                )
                st.caption(
                    "Общий плановый бюджет: "
                    f"**{format_money(total_breakdown, curr)}**"
                )

            st.markdown(
                '<div class="tm-section-title">Детализация бюджета</div>',
                unsafe_allow_html=True,
            )

            for index, row in enumerate(chart_data.to_dict("records")):
                category_name = escape(text_value(row["Категория"]))
                amount_text = escape(text_value(row["Сумма"]))
                percent = as_float(row["Доля"])
                color = BUDGET_COLORS[index % len(BUDGET_COLORS)]

                st.markdown(
                    (
                        '<div class="tm-budget-card">'
                        '<div class="tm-budget-category">'
                        '<span class="tm-budget-dot" '
                        f'style="background:{color};color:{color};"></span>'
                        f'<span>{category_name}</span>'
                        '</div>'
                        '<div>'
                        '<div class="tm-budget-progress">'
                        '<div class="tm-budget-progress-value" '
                        f'style="width:{percent:.1f}%;'
                        f'background:linear-gradient(90deg,{color},'
                        f'rgba(255,255,255,0.9));"></div>'
                        '</div>'
                        '<div class="tm-budget-percent">'
                        f'{percent:.1f}% от бюджета'
                        '</div>'
                        '</div>'
                        '<div class="tm-budget-amount">'
                        f'{amount_text}'
                        '</div>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

# ==========================================================
# ВКЛАДКА 4 — СОВЕТЫ
# ==========================================================

with tab_tips:
    st.markdown(
        '<div class="tm-section-title">✦ Полезное для поездки</div>',
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
            with st.container(border=True):
                st.markdown(
                    f"**{text_value(phrase.get('ru'))}**"
                )
                st.caption(text_value(phrase.get("local")))

    tips = data.get("tips") or {}

    if tips:
        st.subheader("🧭 Советы путешественнику")

        for key, value in tips.items():
            title = TIP_RU.get(key, key)

            st.markdown(
                (
                    '<div class="tm-tip-card">'
                    f'<b>{escape(text_value(title))}</b><br>'
                    f'{escape(text_value(value))}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

# ==========================================================
# ВКЛАДКА 5 — AI-ДАННЫЕ И ЭКСПОРТ
# ==========================================================

with tab_ai:
    st.markdown(
        '<div class="tm-section-title">⌘ Данные AI-маршрута</div>',
        unsafe_allow_html=True,
    )

    st.json(data)

    download_md, download_json = st.columns(2)

    markdown_content = ai.to_markdown(data, curr)
    json_content = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )

    with download_md:
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
