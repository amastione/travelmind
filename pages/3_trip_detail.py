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
import site_access

st.set_page_config(
    page_title="Маршрут поездки",
    page_icon="🗺️",
    layout="wide",
)
site_access.require_site_access()
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
/* ---------- Основа ---------- */

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

/* ---------- Шапка поездки ---------- */

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

/* ---------- Билеты и бронирование ---------- */

.tm-booking-card {
    margin-top: 1.25rem;
    padding: 1.35rem;
    border: 1px solid rgba(103, 232, 249, 0.28);
    border-radius: 22px;
    background:
        radial-gradient(
            circle at 5% 0%,
            rgba(34, 211, 238, 0.13),
            transparent 36%
        ),
        linear-gradient(
            135deg,
            rgba(16, 44, 67, 0.84),
            rgba(29, 28, 70, 0.78)
        );
    box-shadow:
        0 14px 32px rgba(0, 0, 0, 0.14),
        inset 0 1px 0 rgba(255, 255, 255, 0.07);
}

.tm-booking-title {
    color: #FFFFFF;
    font-size: 1.34rem;
    font-weight: 800;
    letter-spacing: -0.035rem;
}

.tm-booking-text {
    margin-top: 0.4rem;
    color: #C9D9EC;
    font-size: 0.96rem;
    line-height: 1.6;
}

.tm-booking-meta {
    display: inline-block;
    margin-top: 0.85rem;
    padding: 0.45rem 0.75rem;
    border: 1px solid rgba(125, 235, 250, 0.22);
    border-radius: 999px;
    background: rgba(34, 211, 238, 0.08);
    color: #A8F1FC;
    font-size: 0.86rem;
    font-weight: 700;
}

.tm-booking-note {
    margin-top: 1rem;
    color: #AFC0D7;
    font-size: 0.82rem;
    line-height: 1.55;
}

/* ---------- Карточки ---------- */

[data-testid="stVerticalBlockBorderWrapper"] {
    border-color: rgba(148, 163, 184, 0.23) !important;
    border-radius: 22px !important;
    background: rgba(15, 23, 42, 0.70) !important;
    box-shadow:
        0 14px 32px rgba(0, 0, 0, 0.12),
        inset 0 1px 0 rgba(255, 255, 255, 0.035);
}

/* ---------- Метрики ---------- */

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
}

/* ---------- Вкладки ---------- */

.stTabs {
    margin-top: 2rem;
}

.stTabs [data-baseweb="tab-list"] {
    display: flex !important;
    align-items: center !important;
    gap: 0.7rem !important;
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
}

.stTabs [data-baseweb="tab"] {
    flex: 0 0 auto !important;
    min-height: 60px !important;
    padding: 0.95rem 1.45rem !important;
    border: 1px solid rgba(228, 240, 255, 0.24) !important;
    border-radius: 19px !important;
    background: rgba(255, 255, 255, 0.085) !important;
    color: #F4F8FE !important;
    font-size: 1.18rem !important;
    font-weight: 800 !important;
    white-space: nowrap !important;
}

.stTabs [data-baseweb="tab"] p {
    color: #F4F8FE !important;
    font-size: 1.18rem !important;
    font-weight: 800 !important;
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
    border: 1px solid rgba(230, 250, 255, 0.92) !important;
    background:
        linear-gradient(
            135deg,
            #0598B7 0%,
            #18CAE4 45%,
            #548AF0 74%,
            #7551DE 100%
        ) !important;
    color: #FFFFFF !important;
}

.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}

/* ---------- Заголовки секций ---------- */

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

/* ==========================================================
   СОБСТВЕННЫЕ КАРТОЧКИ ДНЕЙ
   Здесь нет st.expander, поэтому белый фон исключён.
   ========================================================== */

/* ==========================================================
   БЫСТРЫЕ РАСКРЫВАЕМЫЕ ДНИ МАРШРУТА
   Используем нативный st.expander без полного st.rerun().
   Важно: не стилизуем summary * — это ломает Material Icons.
   ========================================================== */

/* Внешняя тёмная карточка дня */
details[data-testid="stExpander"],
div[data-testid="stExpander"] details {
    overflow: hidden !important;
    margin: 0.9rem 0 !important;
    border: 1px solid rgba(103, 232, 249, 0.26) !important;
    border-radius: 20px !important;
    background: rgba(8, 18, 35, 0.92) !important;
    box-shadow:
        0 12px 28px rgba(0, 0, 0, 0.14),
        inset 0 1px 0 rgba(255, 255, 255, 0.04) !important;
}

/* Заголовок закрытого дня */
details[data-testid="stExpander"] > summary,
div[data-testid="stExpander"] details > summary {
    min-height: 68px !important;
    padding: 1.05rem 1.2rem !important;
    border: 0 !important;
    border-radius: 19px !important;
    background:
        linear-gradient(
            135deg,
            rgba(28, 49, 78, 0.98),
            rgba(13, 27, 51, 0.98)
        ) !important;
    color: #F8FAFC !important;
    cursor: pointer !important;
}

/*
 Текст заголовка. Стилизуем только markdown-контейнер
 и его абзац — не span, не svg и не системную иконку стрелки.
*/
details[data-testid="stExpander"] > summary [data-testid="stMarkdownContainer"],
details[data-testid="stExpander"] > summary [data-testid="stMarkdownContainer"] p,
div[data-testid="stExpander"] details > summary [data-testid="stMarkdownContainer"],
div[data-testid="stExpander"] details > summary [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    color: #F8FAFC !important;
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif !important;
    font-size: 1.04rem !important;
    font-weight: 750 !important;
    line-height: 1.45 !important;
}

/* Стрелка раскрытия: сохраняем Material Icon, меняем только цвет */
details[data-testid="stExpander"] > summary [data-testid="stIconMaterial"],
details[data-testid="stExpander"] > summary .material-symbols-rounded,
details[data-testid="stExpander"] > summary .material-icons,
div[data-testid="stExpander"] details > summary [data-testid="stIconMaterial"],
div[data-testid="stExpander"] details > summary .material-symbols-rounded,
div[data-testid="stExpander"] details > summary .material-icons {
    color: #7DEBFA !important;
}

/* Открытый день */
details[data-testid="stExpander"][open] > summary,
div[data-testid="stExpander"] details[open] > summary {
    border-bottom: 1px solid rgba(103, 232, 249, 0.24) !important;
    border-radius: 19px 19px 0 0 !important;
    background:
        linear-gradient(
            135deg,
            rgba(7, 132, 162, 0.66),
            rgba(53, 69, 166, 0.56)
        ) !important;
}

/* Текст активного заголовка */
details[data-testid="stExpander"][open] > summary [data-testid="stMarkdownContainer"],
details[data-testid="stExpander"][open] > summary [data-testid="stMarkdownContainer"] p,
div[data-testid="stExpander"] details[open] > summary [data-testid="stMarkdownContainer"],
div[data-testid="stExpander"] details[open] > summary [data-testid="stMarkdownContainer"] p {
    color: #FFFFFF !important;
}

/* Контент раскрытого дня — только тёмный фон */
details[data-testid="stExpander"] [data-testid="stExpanderDetails"],
details[data-testid="stExpander"] [data-testid="stExpanderDetails"] > div,
div[data-testid="stExpander"] [data-testid="stExpanderDetails"],
div[data-testid="stExpander"] [data-testid="stExpanderDetails"] > div {
    background: rgba(8, 18, 35, 0.92) !important;
    color: #F8FAFC !important;
}

/* Наведение */
details[data-testid="stExpander"] > summary:hover,
div[data-testid="stExpander"] details > summary:hover {
    background:
        linear-gradient(
            135deg,
            rgba(25, 87, 116, 0.88),
            rgba(55, 57, 132, 0.80)
        ) !important;
}

/* ---------- Активности ---------- */

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

/* ---------- Бюджет ---------- */

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

/* ---------- Кнопки ---------- */

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

.stButton > button:hover,
.stLinkButton > a:hover,
.stDownloadButton > button:hover {
    filter: brightness(1.09);
    transform: translateY(-1px);
}

.stNumberInput input {
    border: 1px solid rgba(148, 163, 184, 0.34) !important;
    border-radius: 11px !important;
    background: rgba(7, 11, 20, 0.70) !important;
    color: #FFFFFF !important;
}

section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] {
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
}

section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] p {
    color: #FFFFFF !important;
    font-size: 0.96rem !important;
    font-weight: 800 !important;
}

@media (max-width: 760px) {
    .block-container {
        padding: 1.5rem 1rem 3rem;
    }

    .tm-hero-title {
        font-size: 1.9rem !important;
    }

    .tm-budget-card {
        grid-template-columns: 1fr;
        gap: 0.72rem;
    }

    .tm-budget-amount {
        text-align: left;
    }
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


def format_date_ru(value):
    """Отображает дату как DD/MM/YYYY."""
    if not value:
        return ""

    try:
        return datetime.strptime(
            str(value)[:10],
            "%Y-%m-%d",
        ).strftime("%d/%m/%Y")
    except ValueError:
        return str(value)


def build_booking_links(destination, start_date, end_date):
    """Создаёт ссылки внешних сервисов для версии TravelMind 1.1."""
    destination_query = quote_plus(str(destination))
    checkin = str(start_date)[:10]
    checkout = str(end_date)[:10]

    hotels_url = (
        "https://www.google.com/travel/hotels"
        f"?q={destination_query}"
        f"&checkin={checkin}"
        f"&checkout={checkout}"
        "&hl=ru"
    )

    map_url = (
        "https://www.google.com/maps/search/?api=1&query="
        f"{destination_query}"
    )

    return {
        "flights": "https://www.aviasales.ru/",
        "trains": "https://www.rzd.ru/",
        "hotels": hotels_url,
        "map": map_url,
    }


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
# БИЛЕТЫ И БРОНИРОВАНИЕ
# ==========================================================

booking_links = build_booking_links(
    destination=destination,
    start_date=trip["start_date"],
    end_date=trip["end_date"],
)

st.markdown(
    f"""
    <div class="tm-booking-card">
        <div class="tm-booking-title">✈️ Билеты и бронирование</div>
        <div class="tm-booking-text">
            Подберите способ добраться до места, найдите проживание
            и откройте направление на карте.
        </div>
        <div class="tm-booking-meta">
            📍 {escape(destination)} · 📅 {escape(start_date_text)} —
            {escape(end_date_text)} · 👥 {people} чел.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

booking_col_1, booking_col_2, booking_col_3, booking_col_4 = st.columns(4)

with booking_col_1:
    st.link_button(
        "✈️ Найти авиабилеты",
        booking_links["flights"],
        use_container_width=True,
    )

with booking_col_2:
    st.link_button(
        "🚆 Билеты РЖД",
        booking_links["trains"],
        use_container_width=True,
    )

with booking_col_3:
    st.link_button(
        "🏨 Найти проживание",
        booking_links["hotels"],
        use_container_width=True,
    )

with booking_col_4:
    st.link_button(
        "⌖ Открыть на карте",
        booking_links["map"],
        use_container_width=True,
    )

st.markdown(
    """
    <div class="tm-booking-note">
        ℹ️ TravelMind не принимает оплату. Бронирование и покупка происходят
        на сайтах внешних сервисов. Стоимость может меняться.
    </div>
    """,
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

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

with metric_1:
    st.metric("Общий бюджет поездки", format_money(total_cost, curr))

with metric_2:
    st.metric("Внесено по факту", format_money(actual_sum, curr))

with metric_3:
    st.metric("План по расходам", format_money(plan_sum, curr))

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
# ВКЛАДКА: МАРШРУТ
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

    # Вместо st.expander используем собственные карточки.
    # Это устраняет белый фон и проблему с нечитаемым заголовком.
        # Нативный expander раскрывается без полного перезапуска приложения.
    # Это быстрее, чем st.button + st.rerun().
    for day in data.get("days", []):
        day_number = day.get("day", "")
        day_date = format_date_ru(day.get("date"))
        day_theme = text_value(day.get("theme"))
        day_vibe = text_value(day.get("vibe"))

        day_header = f"День {day_number} · {day_date}"

        if day_theme:
            day_header += f" — {day_theme}"

        if day_vibe:
            day_header += f" · {day_vibe}"

        with st.expander(
            day_header,
            expanded=(day_number == 1),
        ):
            activities = day.get("activities") or []

            if not activities:
                st.info("Для этого дня пока нет активностей.")

            for activity_index, activity in enumerate(activities):
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

                # Ссылка на карту для конкретной активности.
                if location:
                    activity_map_query = f"{location}, {destination}"

                    activity_map_url = (
                        "https://www.google.com/maps/search/?api=1&query="
                        + quote_plus(activity_map_query)
                    )

                    st.link_button(
                        "⌖ Открыть место на карте",
                        activity_map_url,
                        key=(
                            f"activity_map_{trip_id}_"
                            f"{day_number}_{activity_index}"
                        ),
                        use_container_width=False,
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
# ВКЛАДКА: КАРТА
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
# ВКЛАДКА: БЮДЖЕТ
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
            st.markdown(
                '<div class="tm-section-title">◫ Структура бюджета</div>',
                unsafe_allow_html=True,
            )

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
                            domain=False,
                            ticks=False,
                        ),
                    ),
                    y=alt.Y(
                        "План:Q",
                        axis=alt.Axis(
                            title=None,
                            labelColor="#B9C9DC",
                            domain=False,
                            ticks=False,
                            grid=True,
                            gridColor="#314158",
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
                .configure_view(strokeOpacity=0, fill="transparent")
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
# ВКЛАДКА: СОВЕТЫ
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
# ВКЛАДКА: AI-ДАННЫЕ И ЭКСПОРТ
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
