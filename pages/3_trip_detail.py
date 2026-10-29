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
import branding
import cover_selector
import db
import site_access

st.set_page_config(
    page_title="Маршрут поездки",
    page_icon="🗺️",
    layout="wide",
)

branding.apply_clean_layout()
site_access.require_site_access()

# ==========================================================
# АВТОРИЗАЦИЯ И ЗАГРУЗКА ДАННЫХ
# ==========================================================

user_id = auth.require_auth()
trip_id = st.session_state.get("current_trip_id")

if not trip_id:
    st.warning("Поездка не выбрана. Откройте её из списка путешествий.")

    if st.button(
        "← Перейти к моим путешествиям",
        key="no_trip_go_to_my_trips",
        use_container_width=True,
    ):
        st.switch_page("pages/2_my_trips.py")

    st.stop()

trip = db.get_trip(trip_id, user_id)

if not trip:
    st.error("Поездка не найдена или была удалена.")

    if st.button(
        "← Перейти к моим путешествиям",
        key="missing_trip_go_to_my_trips",
        use_container_width=True,
    ):
        st.switch_page("pages/2_my_trips.py")

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

/* ---------- Фото-обложка маршрута ---------- */

.tm-trip-hero-cover {
    position: relative;
    overflow: hidden;
    min-height: 330px;
    margin-top: 1rem;
    padding: 2.1rem;
    border: 1px solid rgba(172, 226, 245, 0.30);
    border-radius: 26px;
    background-color: #0B1D3A;
    background-repeat: no-repeat;
    background-size: cover;
    background-position: center;
    box-shadow:
        0 20px 44px rgba(0, 0, 0, 0.22),
        inset 0 1px 0 rgba(255, 255, 255, 0.13);
}

.tm-trip-hero-cover::before {
    position: absolute;
    inset: 0;
    z-index: 0;
    background:
        linear-gradient(
            90deg,
            rgba(3, 9, 23, 0.94) 0%,
            rgba(4, 13, 31, 0.82) 43%,
            rgba(6, 15, 34, 0.37) 72%,
            rgba(6, 15, 34, 0.20) 100%
        ),
        linear-gradient(
            0deg,
            rgba(3, 9, 23, 0.50) 0%,
            transparent 56%
        );
    content: "";
}

.tm-trip-hero-content {
    position: relative;
    z-index: 1;
    max-width: 760px;
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
    background: rgba(64, 83, 116, 0.50) !important;
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
/*
 Streamlit для неактивных вкладок иногда автоматически делает
 текст полупрозрачным. Принудительно оставляем названия белыми.
*/
.stTabs [data-baseweb="tab"],
.stTabs button[role="tab"],
.stTabs [role="tab"] {
    opacity: 1 !important;
    color: #FFFFFF !important;
}

.stTabs [data-baseweb="tab"] p,
.stTabs button[role="tab"] p,
.stTabs [role="tab"] p,
.stTabs [data-baseweb="tab"] [data-testid="stMarkdownContainer"],
.stTabs [data-baseweb="tab"] [data-testid="stMarkdownContainer"] p {
    opacity: 1 !important;
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
    text-shadow: 0 1px 10px rgba(255, 255, 255, 0.08) !important;
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

/* ---------- Дни маршрута ---------- */

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

details[data-testid="stExpander"] > summary [data-testid="stMarkdownContainer"],
details[data-testid="stExpander"] > summary [data-testid="stMarkdownContainer"] p,
div[data-testid="stExpander"] details > summary [data-testid="stMarkdownContainer"],
div[data-testid="stExpander"] details > summary [data-testid="stMarkdownContainer"] p {
    margin: 0 !important;
    padding: 0 !important;
    background: transparent !important;
    color: #F8FAFC !important;
    font-size: 1.04rem !important;
    font-weight: 750 !important;
    line-height: 1.45 !important;
}

details[data-testid="stExpander"] > summary [data-testid="stIconMaterial"],
details[data-testid="stExpander"] > summary .material-symbols-rounded,
details[data-testid="stExpander"] > summary .material-icons,
div[data-testid="stExpander"] details > summary [data-testid="stIconMaterial"],
div[data-testid="stExpander"] details > summary .material-symbols-rounded,
div[data-testid="stExpander"] details > summary .material-icons {
    color: #7DEBFA !important;
}

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

details[data-testid="stExpander"] [data-testid="stExpanderDetails"],
details[data-testid="stExpander"] [data-testid="stExpanderDetails"] > div,
div[data-testid="stExpander"] [data-testid="stExpanderDetails"],
div[data-testid="stExpander"] [data-testid="stExpanderDetails"] > div {
    background: rgba(8, 18, 35, 0.92) !important;
    color: #F8FAFC !important;
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

/* ---------- Диалог с AI ---------- */

.tm-ai-edit-card {
    margin-top: 0.5rem;
    padding: 1.45rem;
    border: 1px solid rgba(103, 232, 249, 0.30);
    border-radius: 22px;
    background:
        radial-gradient(
            circle at 5% 0%,
            rgba(34, 211, 238, 0.13),
            transparent 38%
        ),
        linear-gradient(
            135deg,
            rgba(13, 43, 65, 0.84),
            rgba(30, 25, 69, 0.78)
        );
    box-shadow:
        0 16px 36px rgba(0, 0, 0, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.07);
}

.tm-ai-edit-title {
    color: #FFFFFF;
    font-size: 1.42rem;
    font-weight: 800;
    letter-spacing: -0.035rem;
}

.tm-ai-edit-text {
    margin-top: 0.45rem;
    color: #C9D9EC;
    font-size: 0.97rem;
    line-height: 1.62;
}

.tm-ai-edit-warning {
    margin-top: 1rem;
    padding: 0.85rem 0.95rem;
    border: 1px solid rgba(253, 230, 138, 0.23);
    border-radius: 13px;
    background: rgba(245, 158, 11, 0.08);
    color: #FDE9A7;
    font-size: 0.88rem;
    line-height: 1.55;
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

/* ---------- Форма диалога с AI ---------- */

[data-testid="stForm"] {
    padding: 1.25rem !important;
    border: 1px solid rgba(103, 232, 249, 0.24) !important;
    border-radius: 20px !important;
    background:
        linear-gradient(
            135deg,
            rgba(14, 33, 57, 0.92),
            rgba(20, 20, 52, 0.90)
        ) !important;
    box-shadow:
        0 14px 30px rgba(0, 0, 0, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

[data-testid="stForm"] [data-testid="stWidgetLabel"] p,
[data-testid="stForm"] label {
    color: #DCEBFA !important;
    font-size: 0.98rem !important;
    font-weight: 750 !important;
}

[data-testid="stForm"] textarea,
[data-testid="stTextArea"] textarea {
    min-height: 130px !important;
    border: 1px solid rgba(148, 163, 184, 0.38) !important;
    border-radius: 14px !important;
    background: rgba(5, 12, 26, 0.82) !important;
    color: #F8FAFC !important;
    font-size: 0.98rem !important;
    line-height: 1.55 !important;
}

[data-testid="stForm"] textarea::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #7D91AE !important;
    opacity: 1 !important;
}

[data-testid="stForm"] textarea:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #22D3EE !important;
    box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.15) !important;
    outline: none !important;
}

[data-testid="stFormSubmitButton"] > button,
.stFormSubmitButton > button {
    width: 100% !important;
    min-height: 52px !important;
    border: 1px solid rgba(235, 254, 255, 0.56) !important;
    border-radius: 14px !important;
    background:
        radial-gradient(
            circle at 20% 0%,
            rgba(255, 255, 255, 0.25),
            transparent 40%
        ),
        linear-gradient(
            135deg,
            #06AFCB 0%,
            #22D3EE 46%,
            #538CF0 73%,
            #8558E9 100%
        ) !important;
    color: #FFFFFF !important;
    font-size: 1rem !important;
    font-weight: 800 !important;
}

/* ==========================================================
   ФАКТИЧЕСКИЕ РАСХОДЫ: КОМПАКТНЫЕ КНОПКИ «− / +»
   ========================================================== */

[data-testid="stNumberInput"],
.stNumberInput {
    width: 100% !important;
}

/*
 Главный контейнер не должен обрезать отдельные скруглённые кнопки.
*/
[data-testid="stNumberInput"] [data-baseweb="input"],
.stNumberInput [data-baseweb="input"] {
    overflow: visible !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}

/*
 Поле суммы. Высота соответствует кнопкам, чтобы контрол
 выглядел единым по сетке, но не «слитым».
*/
[data-testid="stNumberInput"] input,
.stNumberInput input {
    min-width: 0 !important;
    height: 40px !important;
    min-height: 40px !important;
    padding: 0 0.5rem !important;
    border: 1px solid rgba(183, 214, 237, 0.80) !important;
    border-radius: 11px !important;
    background: rgba(10, 22, 39, 0.92) !important;
    color: #FFFFFF !important;
    font-size: 0.92rem !important;
    font-weight: 750 !important;
    text-align: center !important;
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

[data-testid="stNumberInput"] input:focus,
.stNumberInput input:focus {
    border-color: #22D3EE !important;
    outline: none !important;
    box-shadow:
        0 0 0 3px rgba(34, 211, 238, 0.14),
        inset 0 1px 0 rgba(255, 255, 255, 0.06) !important;
}

/*
 Внутренний контейнер Streamlit с двумя кнопками.
 Именно этот блок разделяет «−» и «+», не позволяя им сливаться
 и не обрезая нижние скругления.
*/
[data-testid="stNumberInput"] [data-baseweb="input-spinner"],
.stNumberInput [data-baseweb="input-spinner"] {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    margin-left: 7px !important;
    overflow: visible !important;
}

/*
 Компактные отдельные кнопки.
 Все 4 угла скруглены; размер уменьшен, чтобы элементы
 гарантированно помещались в строку расходов.
*/
[data-testid="stNumberInput"] [data-baseweb="input-spinner"] button,
[data-testid="stNumberInput"] button,
.stNumberInput [data-baseweb="input-spinner"] button,
.stNumberInput button {
    display: inline-flex !important;
    flex: 0 0 40px !important;
    align-items: center !important;
    justify-content: center !important;
    box-sizing: border-box !important;
    width: 40px !important;
    min-width: 40px !important;
    max-width: 40px !important;
    height: 40px !important;
    min-height: 40px !important;
    max-height: 40px !important;
    margin: 0 !important;
    padding: 0 !important;
    border: 1px solid rgba(125, 235, 250, 0.46) !important;
    border-radius: 11px !important;
    background:
        linear-gradient(
            145deg,
            rgba(24, 73, 100, 0.98),
            rgba(26, 37, 87, 0.98)
        ) !important;
    color: #B4F5FF !important;
    box-shadow:
        0 5px 12px rgba(0, 0, 0, 0.18),
        inset 0 1px 0 rgba(255, 255, 255, 0.12) !important;
    overflow: visible !important;
    transition:
        transform 160ms ease,
        filter 160ms ease,
        background 160ms ease,
        border-color 160ms ease,
        box-shadow 160ms ease !important;
}

/*
 Убираем старые стили, которые в некоторых версиях Streamlit
 делают левую или правую кнопку частью общей «капсулы».
*/
[data-testid="stNumberInput"] button:first-child,
[data-testid="stNumberInput"] button:last-child,
.stNumberInput button:first-child,
.stNumberInput button:last-child {
    border-radius: 11px !important;
    border-left: 1px solid rgba(125, 235, 250, 0.46) !important;
    border-right: 1px solid rgba(125, 235, 250, 0.46) !important;
}

/*
 Символы меньше и строго по центру.
 Значение line-height равно размеру контейнера и исключает
 смещение вверх/вниз у Material Icons.
*/
[data-testid="stNumberInput"] button svg,
[data-testid="stNumberInput"] button [data-testid="stIconMaterial"],
[data-testid="stNumberInput"] button .material-symbols-rounded,
[data-testid="stNumberInput"] button .material-icons,
.stNumberInput button svg,
.stNumberInput button [data-testid="stIconMaterial"],
.stNumberInput button .material-symbols-rounded,
.stNumberInput button .material-icons {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 16px !important;
    min-width: 16px !important;
    height: 16px !important;
    min-height: 16px !important;
    margin: 0 !important;
    padding: 0 !important;
    color: #B4F5FF !important;
    fill: currentColor !important;
    font-size: 1rem !important;
    line-height: 16px !important;
    text-align: center !important;
}

/* Hover */
[data-testid="stNumberInput"] button:hover,
.stNumberInput button:hover {
    border-color: rgba(237, 254, 255, 0.90) !important;
    background:
        linear-gradient(
            135deg,
            #078EAA 0%,
            #1CC7DF 50%,
            #6B5EE6 100%
        ) !important;
    color: #FFFFFF !important;
    box-shadow:
        0 8px 17px rgba(34, 211, 238, 0.21),
        inset 0 1px 0 rgba(255, 255, 255, 0.24) !important;
    transform: translateY(-1px) !important;
}

[data-testid="stNumberInput"] button:hover svg,
[data-testid="stNumberInput"] button:hover [data-testid="stIconMaterial"],
[data-testid="stNumberInput"] button:hover .material-symbols-rounded,
[data-testid="stNumberInput"] button:hover .material-icons,
.stNumberInput button:hover svg,
.stNumberInput button:hover [data-testid="stIconMaterial"],
.stNumberInput button:hover .material-symbols-rounded,
.stNumberInput button:hover .material-icons {
    color: #FFFFFF !important;
}

/* Нажатие */
[data-testid="stNumberInput"] button:active,
.stNumberInput button:active {
    transform: translateY(0) scale(0.95) !important;
}

/* Убираем системные стрелки внутри поля */
[data-testid="stNumberInput"] input::-webkit-outer-spin-button,
[data-testid="stNumberInput"] input::-webkit-inner-spin-button {
    margin: 0 !important;
    appearance: none !important;
}

[data-testid="stNumberInput"] input[type="number"] {
    appearance: textfield !important;
    -moz-appearance: textfield !important;
}

/* На мобильных устройствах контрол ещё компактнее */
@media (max-width: 640px) {
    [data-testid="stNumberInput"] input,
    .stNumberInput input {
        height: 38px !important;
        min-height: 38px !important;
        font-size: 0.88rem !important;
    }

    [data-testid="stNumberInput"] [data-baseweb="input-spinner"],
    .stNumberInput [data-baseweb="input-spinner"] {
        gap: 5px !important;
        margin-left: 5px !important;
    }

    [data-testid="stNumberInput"] button,
    .stNumberInput button {
        flex-basis: 38px !important;
        width: 38px !important;
        min-width: 38px !important;
        max-width: 38px !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        border-radius: 10px !important;
    }
}

/* ==========================================================
   КАРТОЧКИ ФАКТИЧЕСКИХ РАСХОДОВ
   ========================================================== */

.tm-expense-heading {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1rem;
}

.tm-expense-title {
    color: #F8FAFC;
    font-size: 1.04rem;
    font-weight: 800;
    line-height: 1.45;
}

.tm-expense-day {
    flex: 0 0 auto;
    padding: 0.34rem 0.68rem;
    border: 1px solid rgba(103, 232, 249, 0.25);
    border-radius: 999px;
    background: rgba(34, 211, 238, 0.08);
    color: #A8F1FC;
    font-size: 0.78rem;
    font-weight: 800;
    white-space: nowrap;
}

.tm-expense-label {
    margin-bottom: 0.3rem;
    color: #AABDD3;
    font-size: 0.78rem;
    font-weight: 750;
    letter-spacing: 0.03rem;
    text-transform: uppercase;
}

.tm-expense-plan-value {
    color: #FFFFFF;
    font-size: 1.2rem;
    font-weight: 800;
}

.tm-expense-status {
    display: inline-flex;
    align-items: center;
    min-height: 28px;
    margin-top: 0.55rem;
    padding: 0.28rem 0.6rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 999px;
    background: rgba(148, 163, 184, 0.08);
    color: #B9C8D9;
    font-size: 0.78rem;
    font-weight: 700;
}

.tm-expense-status.is-saving {
    border-color: rgba(74, 222, 128, 0.25);
    background: rgba(74, 222, 128, 0.10);
    color: #A7F3D0;
}

.tm-expense-status.is-over {
    border-color: rgba(251, 113, 133, 0.28);
    background: rgba(251, 113, 133, 0.10);
    color: #FDA4AF;
}

.tm-expense-fact-label {
    margin-bottom: 0.45rem;
    color: #AABDD3;
    font-size: 0.78rem;
    font-weight: 750;
    letter-spacing: 0.03rem;
    text-transform: uppercase;
}

/* Сохранение в карточке расхода */
.tm-expense-save-note {
    margin-top: 0.55rem;
    color: #91A6BF;
    font-size: 0.76rem;
    line-height: 1.45;
}

@media (max-width: 760px) {
    .tm-expense-heading {
        align-items: flex-start;
        flex-direction: column;
        gap: 0.55rem;
    }

    .tm-expense-title {
        font-size: 1rem;
    }
}
/* ---------- Сводка бюджета поездки ---------- */

.tm-budget-summary {
    margin: 0.4rem 0 1.35rem;
    padding: 1.4rem;
    border: 1px solid rgba(103, 232, 249, 0.30);
    border-radius: 22px;
    background:
        radial-gradient(
            circle at 8% 0%,
            rgba(34, 211, 238, 0.16),
            transparent 36%
        ),
        radial-gradient(
            circle at 100% 100%,
            rgba(139, 92, 246, 0.16),
            transparent 38%
        ),
        linear-gradient(
            135deg,
            rgba(16, 42, 65, 0.88),
            rgba(25, 22, 62, 0.88)
        );
    box-shadow:
        0 15px 34px rgba(0, 0, 0, 0.16),
        inset 0 1px 0 rgba(255, 255, 255, 0.08);
}

.tm-budget-summary-label {
    color: #A8F1FC;
    font-size: 0.78rem;
    font-weight: 800;
    letter-spacing: 0.08rem;
    text-transform: uppercase;
}

.tm-budget-summary-total {
    margin-top: 0.32rem;
    color: #FFFFFF;
    font-size: 2rem;
    font-weight: 850;
    letter-spacing: -0.06rem;
}

.tm-budget-summary-caption {
    margin-top: 0.28rem;
    color: #C4D4E8;
    font-size: 0.9rem;
    line-height: 1.5;
}

.tm-budget-summary-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin-top: 1.2rem;
}

.tm-budget-summary-item {
    padding: 0.8rem 0.9rem;
    border: 1px solid rgba(190, 218, 242, 0.14);
    border-radius: 15px;
    background: rgba(4, 13, 29, 0.32);
}

.tm-budget-summary-item-label {
    color: #AFC0D6;
    font-size: 0.76rem;
    font-weight: 750;
    letter-spacing: 0.03rem;
    text-transform: uppercase;
}

.tm-budget-summary-item-value {
    margin-top: 0.28rem;
    color: #FFFFFF;
    font-size: 1.08rem;
    font-weight: 800;
}

.tm-budget-summary-item-value.is-positive {
    color: #86EFAC;
}

.tm-budget-summary-item-value.is-warning {
    color: #FDE68A;
}

.tm-budget-summary-item-value.is-danger {
    color: #FDA4AF;
}

.tm-budget-progress-track {
    width: 100%;
    height: 12px;
    overflow: hidden;
    margin-top: 1rem;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 999px;
    background: rgba(4, 12, 26, 0.58);
}

.tm-budget-progress-value {
    height: 100%;
    min-width: 0;
    border-radius: inherit;
    box-shadow: 0 0 16px currentColor;
}

.tm-budget-progress-text {
    margin-top: 0.55rem;
    color: #C8D8EB;
    font-size: 0.84rem;
    font-weight: 700;
}

@media (max-width: 760px) {
    .tm-budget-summary {
        padding: 1.15rem;
        border-radius: 18px;
    }

    .tm-budget-summary-total {
        font-size: 1.7rem;
    }

    .tm-budget-summary-grid {
        grid-template-columns: 1fr;
    }
}
/* ---------- История ручных расходов ---------- */

.tm-manual-expense-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin: 0.65rem 0;
    padding: 0.95rem 1rem;
    border: 1px solid rgba(167, 139, 250, 0.30);
    border-radius: 16px;
    background:
        linear-gradient(
            135deg,
            rgba(66, 42, 112, 0.30),
            rgba(12, 29, 53, 0.72)
        );
}

.tm-manual-expense-main {
    min-width: 0;
}

.tm-manual-expense-title {
    color: #FFFFFF;
    font-size: 1rem;
    font-weight: 800;
    line-height: 1.4;
}

.tm-manual-expense-meta {
    margin-top: 0.3rem;
    color: #B9C9DF;
    font-size: 0.82rem;
    font-weight: 650;
}

.tm-manual-expense-amount {
    flex: 0 0 auto;
    color: #A8F1FC;
    font-size: 1.08rem;
    font-weight: 850;
    text-align: right;
    white-space: nowrap;
}

.tm-manual-expense-plan {
    margin-top: 0.25rem;
    color: #AABDD3;
    font-size: 0.76rem;
    font-weight: 650;
}

@media (max-width: 760px) {
    .tm-manual-expense-card {
        align-items: flex-start;
        flex-direction: column;
    }

    .tm-manual-expense-amount {
        text-align: left;
    }
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

@media (max-width: 760px) {
    .block-container {
        padding: 1.5rem 1rem 3rem;
    }

    .tm-trip-hero-cover {
        min-height: 290px;
        padding: 1.45rem;
        border-radius: 21px;
        background-position: 62% center;
    }

    .tm-trip-hero-content {
        max-width: 100%;
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

@media (max-width: 640px) {
    [data-testid="stNumberInput"] [data-baseweb="input"],
    .stNumberInput [data-baseweb="input"] {
        gap: 0.3rem !important;
    }

    [data-testid="stNumberInput"] button,
    .stNumberInput button {
        flex-basis: 42px !important;
        width: 42px !important;
        min-width: 42px !important;
        height: 42px !important;
        min-height: 42px !important;
        border-radius: 10px !important;
    }

    [data-testid="stNumberInput"] input,
    .stNumberInput input {
        min-height: 42px !important;
        height: 42px !important;
        border-radius: 10px !important;
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


def calculate_distance_km(lat_1, lon_1, lat_2, lon_2):
    """
    Рассчитывает примерное расстояние между двумя точками по прямой
    по формуле гаверсинуса. Результат — в километрах.
    """
    from math import asin, cos, radians, sin, sqrt

    earth_radius_km = 6371.0

    lat_1_rad = radians(float(lat_1))
    lon_1_rad = radians(float(lon_1))
    lat_2_rad = radians(float(lat_2))
    lon_2_rad = radians(float(lon_2))

    delta_lat = lat_2_rad - lat_1_rad
    delta_lon = lon_2_rad - lon_1_rad

    distance_formula = (
        sin(delta_lat / 2) ** 2
        + cos(lat_1_rad)
        * cos(lat_2_rad)
        * sin(delta_lon / 2) ** 2
    )

    return earth_radius_km * 2 * asin(sqrt(distance_formula))
    
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

cover_profile = text_value(data.get("cover_profile")).strip().lower()

travel_type = text_value(
    data.get("travel_type")
    or data.get("trip_type")
    or data.get("type")
    or data.get("category")
)

hero_cover_url = cover_selector.get_cover_data_url(
    destination=destination,
    start_date=trip["start_date"],
    travel_type=travel_type,
    cover_profile=cover_profile,
)

if hero_cover_url:
    safe_hero_cover_url = escape(hero_cover_url, quote=True)

    hero_background_style = f"""
        background-image:
            url('{safe_hero_cover_url}');
    """
else:
    hero_background_style = """
        background-image:
            linear-gradient(
                135deg,
                #0B1D3A 0%,
                #145DA0 52%,
                #6D28D9 100%
            );
    """

navigation_left, navigation_space = st.columns([1.35, 2.65])

with navigation_left:
    if st.button(
        "← К моим путешествиям",
        key="hero_go_to_my_trips",
        use_container_width=True,
    ):
        st.switch_page("pages/2_my_trips.py")

overview_html = ""

if overview:
    overview_html = (
        f'<div class="tm-overview-box">{escape(overview)}</div>'
    )

mood_html = ""

if mood_reason:
    mood_html = (
        f'<div class="tm-mood-box">🙂 {escape(mood_reason)}</div>'
    )

st.markdown(
    (
        f'<div class="tm-trip-hero-cover" style="{hero_background_style}">'
        '<div class="tm-trip-hero-content">'
        '<div class="tm-hero-label">'
        'TravelMind AI · Персональный маршрут'
        '</div>'
        f'<div class="tm-hero-title">🗺️ {escape(trip_title)}</div>'
        '<div class="tm-hero-meta">'
        f'📍 {escape(destination)}<br>'
        f'📅 {escape(start_date_text)} — {escape(end_date_text)} '
        f'· 👥 {people} чел.'
        '</div>'
        f'{overview_html}'
        f'{mood_html}'
        '</div>'
        '</div>'
    ),
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

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

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

tab_route, tab_map, tab_budget, tab_tips, tab_edit, tab_ai = st.tabs(
    [
        "▦  Маршрут по дням",
        "⌖  Карта поездки",
        "◫  Бюджет и расходы",
        "✦  Советы",
        "💬  Изменить с AI",
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
# ==========================================================
# ВКЛАДКА: КАРТА И АНАЛИЗ ЛОГИСТИКИ
# ==========================================================

with tab_map:
    st.markdown(
        '<div class="tm-section-title">⌖ Карта маршрута</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="tm-section-text">'
            'Карта показывает последовательность активностей и помогает '
            'оценить логистику каждого дня. Выберите день, чтобы оставить '
            'на карте только нужные точки.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    map_type_colors = {
        "A": "#818CF8",
        "F": "#FB923C",
        "T": "#94A3B8",
        "S": "#A78BFA",
        "L": "#2DD4BF",
        "H": "#F472B6",
        "W": "#FACC15",
    }

    all_map_points = []

    for day in data.get("days", []):
        day_number = day.get("day")
        day_date = format_date_ru(day.get("date"))
        activities = day.get("activities") or []

        for activity_index, activity in enumerate(activities, start=1):
            try:
                lat = float(activity.get("lat"))
                lon = float(activity.get("lon"))
            except (TypeError, ValueError):
                continue

            if not (-90 <= lat <= 90 and -180 <= lon <= 180):
                continue

            all_map_points.append(
                {
                    "day": day_number,
                    "date": day_date,
                    "order": activity_index,
                    "lat": lat,
                    "lon": lon,
                    "title": text_value(
                        activity.get("title"),
                        "Активность",
                    ),
                    "type": text_value(activity.get("type"), "A"),
                    "time": text_value(activity.get("time"), "—"),
                    "location": text_value(activity.get("location"), "—"),
                    "description": text_value(
                        activity.get("description"),
                    ),
                    "cost": as_float(activity.get("cost"), 0),
                    "duration": text_value(
                        activity.get("duration_min"),
                        "—",
                    ),
                }
            )

    if not all_map_points:
        st.info(
            "Для этой поездки AI не вернул координаты мест. "
            "Откройте места по отдельным ссылкам во вкладке "
            "«Маршрут по дням»."
        )

    else:
        available_map_days = sorted(
            {
                point["day"]
                for point in all_map_points
                if point["day"] is not None
            }
        )

        map_filter_col, map_info_col = st.columns([1.2, 2.8])

        with map_filter_col:
            selected_map_day = st.selectbox(
                "Показать на карте",
                options=["Все дни"] + available_map_days,
                key=f"map_day_filter_{trip_id}",
                format_func=lambda value: (
                    value
                    if value == "Все дни"
                    else f"День {value}"
                ),
            )

        if selected_map_day == "Все дни":
            visible_map_points = all_map_points
            map_filter_caption = (
                f"На карте показано мест: {len(visible_map_points)}"
            )
        else:
            visible_map_points = [
                point
                for point in all_map_points
                if point["day"] == selected_map_day
            ]

            map_filter_caption = (
                f"День {selected_map_day}: "
                f"показано мест — {len(visible_map_points)}"
            )

        with map_info_col:
            st.markdown(
                (
                    '<div style="padding-top:2rem; color:#AFC0D7; '
                    'font-size:0.9rem; font-weight:650;">'
                    f'{escape(map_filter_caption)}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

        center_lat = sum(
            point["lat"]
            for point in visible_map_points
        ) / len(visible_map_points)

        center_lon = sum(
            point["lon"]
            for point in visible_map_points
        ) / len(visible_map_points)

        # OpenStreetMap не требует API-ключа.
        fmap = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12,
            tiles="OpenStreetMap",
            attr="© OpenStreetMap contributors",
            attribution_control=False,
            control_scale=True,
        )

        points_by_day = defaultdict(list)

        for point in visible_map_points:
            points_by_day[point["day"]].append(point)

        # Линии между активностями одного дня.
        for day_number, day_points in points_by_day.items():
            sorted_day_points = sorted(
                day_points,
                key=lambda item: item["order"],
            )

            if len(sorted_day_points) > 1:
                folium.PolyLine(
                    locations=[
                        [point["lat"], point["lon"]]
                        for point in sorted_day_points
                    ],
                    color="#22D3EE",
                    weight=4,
                    opacity=0.8,
                    tooltip=f"Маршрут: день {day_number}",
                ).add_to(fmap)

        # Пронумерованные маркеры.
        for point in visible_map_points:
            marker_color = map_type_colors.get(
                point["type"],
                "#22D3EE",
            )

            popup_html = (
                '<div style="min-width:220px; font-family:Arial,sans-serif;'
                'color:#172033; line-height:1.45;">'
                '<div style="font-size:12px; color:#64748B; '
                'font-weight:700; margin-bottom:4px;">'
                f'ДЕНЬ {escape(str(point["day"]))} · '
                f'{escape(point["time"])}'
                '</div>'
                '<div style="font-size:16px; font-weight:800; '
                'margin-bottom:6px;">'
                f'{escape(point["title"])}'
                '</div>'
                '<div style="font-size:13px; margin-bottom:5px;">'
                f'📍 {escape(point["location"])}'
                '</div>'
                '<div style="font-size:13px; margin-bottom:5px;">'
                f'⏱️ {escape(point["duration"])} мин · '
                f'💳 ~{escape(format_money(point["cost"], curr))}'
                '</div>'
                '<div style="font-size:13px; color:#475569;">'
                f'{escape(point["description"])}'
                '</div>'
                '</div>'
            )

            marker_html = (
                '<div style="'
                'width:32px; height:32px; '
                'display:flex; align-items:center; justify-content:center; '
                'border:2px solid rgba(255,255,255,0.95); '
                'border-radius:50%; '
                f'background:{marker_color}; '
                'color:#FFFFFF; '
                'font-family:Arial,sans-serif; '
                'font-size:14px; font-weight:800; '
                'box-shadow:0 3px 12px rgba(0,0,0,0.35);'
                '">'
                f'{point["order"]}'
                '</div>'
            )

            folium.Marker(
                location=[point["lat"], point["lon"]],
                tooltip=(
                    f'День {point["day"]} · '
                    f'{point["time"]} · {point["title"]}'
                ),
                popup=folium.Popup(
                    popup_html,
                    max_width=290,
                ),
                icon=folium.DivIcon(
                    html=marker_html,
                    icon_size=(32, 32),
                    icon_anchor=(16, 16),
                ),
            ).add_to(fmap)

        if len(visible_map_points) > 1:
            fmap.fit_bounds(
                [
                    [point["lat"], point["lon"]]
                    for point in visible_map_points
                ],
                padding=(35, 35),
            )

        # Скрываем стандартную подпись Leaflet внутри карты:
        # источник указан под картой.
        fmap.get_root().html.add_child(
            folium.Element(
                """
                <style>
                    .leaflet-control-attribution {
                        display: none !important;
                    }
                </style>
                """
            )
        )

        legend_html = """
        <div style="
            position: fixed;
            bottom: 26px;
            left: 18px;
            z-index: 9999;
            width: 190px;
            padding: 12px 14px;
            border: 1px solid rgba(148,163,184,0.42);
            border-radius: 12px;
            background: rgba(15,23,42,0.92);
            color: #F8FAFC;
            font-family: Arial, sans-serif;
            font-size: 12px;
            line-height: 1.8;
            box-shadow: 0 8px 22px rgba(0,0,0,0.30);
        ">
            <div style="
                margin-bottom:4px;
                color:#FFFFFF;
                font-size:13px;
                font-weight:800;
            ">
                Типы активностей
            </div>
            <div><span style="color:#818CF8;">●</span> Достопримечательность</div>
            <div><span style="color:#FB923C;">●</span> Еда</div>
            <div><span style="color:#94A3B8;">●</span> Транспорт</div>
            <div><span style="color:#A78BFA;">●</span> Проживание</div>
            <div><span style="color:#2DD4BF;">●</span> Отдых и прогулка</div>
            <div><span style="color:#F472B6;">●</span> Покупки</div>
            <div><span style="color:#FACC15;">●</span> Яркое впечатление</div>
        </div>
        """

        fmap.get_root().html.add_child(
            folium.Element(legend_html)
        )

        with st.container(border=True):
            st_folium(
                fmap,
                use_container_width=True,
                height=560,
                returned_objects=[],
                key=f"travel_route_map_{trip_id}_{selected_map_day}",
            )

        st.caption(
            "Цифра на точке — порядок активности в рамках выбранного дня. "
            "Линии соединяют места в последовательности маршрута. "
            "Картографические данные: © OpenStreetMap contributors."
        )

        # ==================================================
        # АНАЛИЗ ЛОГИСТИКИ
        # ==================================================

        st.markdown(
            '<div class="tm-section-title">✨ Анализ логистики</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            (
                '<div class="tm-section-text">'
                'TravelMind оценивает примерные расстояния между точками '
                'маршрута. Расчёт выполняется по прямой между координатами, '
                'поэтому реальный путь по дорогам может быть длиннее.'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        # Используется тот же фильтр, что и для карты.
        # Отдельный selectbox здесь не нужен.
        logistics_by_day = {}

        for day_number, day_points in points_by_day.items():
            ordered_points = sorted(
                day_points,
                key=lambda item: item["order"],
            )

            total_distance_km = 0.0
            longest_jump_km = 0.0
            longest_jump_from = None
            longest_jump_to = None

            for point_index in range(len(ordered_points) - 1):
                current_point = ordered_points[point_index]
                next_point = ordered_points[point_index + 1]

                segment_distance_km = calculate_distance_km(
                    current_point["lat"],
                    current_point["lon"],
                    next_point["lat"],
                    next_point["lon"],
                )

                total_distance_km += segment_distance_km

                if segment_distance_km > longest_jump_km:
                    longest_jump_km = segment_distance_km
                    longest_jump_from = current_point
                    longest_jump_to = next_point

            logistics_by_day[day_number] = {
                "points_count": len(ordered_points),
                "total_distance_km": total_distance_km,
                "longest_jump_km": longest_jump_km,
                "longest_jump_from": longest_jump_from,
                "longest_jump_to": longest_jump_to,
            }

        if not logistics_by_day:
            st.info(
                "Для анализа нужно минимум две активности с координатами "
                "внутри одного дня."
            )

        else:
            for day_number in sorted(logistics_by_day.keys()):
                logistics = logistics_by_day[day_number]

                points_count = logistics["points_count"]
                total_distance_km = logistics["total_distance_km"]
                longest_jump_km = logistics["longest_jump_km"]
                longest_from = logistics["longest_jump_from"]
                longest_to = logistics["longest_jump_to"]

                if points_count < 2:
                    status_icon = "🔵"
                    status_title = "Недостаточно точек для оценки"
                    status_text = (
                        "В этот день есть только одна активность "
                        "с координатами."
                    )
                    status_type = "info"

                elif longest_jump_km >= 8 or total_distance_km >= 18:
                    status_icon = "🔴"
                    status_title = "Логистика требует оптимизации"
                    status_text = (
                        "В маршруте есть заметно удалённые точки. "
                        "Стоит изменить порядок активностей или заменить "
                        "одну из них альтернативой ближе к остальным."
                    )
                    status_type = "error"

                elif longest_jump_km >= 4 or total_distance_km >= 10:
                    status_icon = "🟡"
                    status_title = "Есть длинные перемещения"
                    status_text = (
                        "Маршрут выполним, но стоит заложить время "
                        "на транспорт и переходы."
                    )
                    status_type = "warning"

                else:
                    status_icon = "🟢"
                    status_title = "Логистика выглядит комфортной"
                    status_text = (
                        "Точки расположены достаточно близко. "
                        "Маршрут подходит для спокойного городского дня."
                    )
                    status_type = "success"

                with st.container(border=True):
                    st.markdown(
                        f"### {status_icon} День {day_number} · "
                        f"{status_title}"
                    )

                    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)

                    with metric_col_1:
                        st.metric(
                            "Точек с координатами",
                            points_count,
                        )

                    with metric_col_2:
                        st.metric(
                            "Примерный путь",
                            f"{total_distance_km:.1f} км",
                        )

                    with metric_col_3:
                        st.metric(
                            "Самый длинный переезд",
                            f"{longest_jump_km:.1f} км",
                        )

                    if status_type == "success":
                        st.success(status_text)
                    elif status_type == "warning":
                        st.warning(status_text)
                    elif status_type == "error":
                        st.error(status_text)
                    else:
                        st.info(status_text)

                    if (
                        longest_from
                        and longest_to
                        and longest_jump_km >= 4
                    ):
                        st.markdown(
                            (
                                f"**На что обратить внимание:** между "
                                f"«{longest_from['title']}» и "
                                f"«{longest_to['title']}» примерно "
                                f"**{longest_jump_km:.1f} км** по прямой."
                            )
                        )

                    if (
                        points_count >= 2
                        and (
                            longest_jump_km >= 4
                            or total_distance_km >= 10
                        )
                    ):
                        logistics_request = (
                            f"Оптимизируй логистику дня {day_number}. "
                            "Сохрани ключевые впечатления и бюджет, "
                            "но переставь активности в более удобном "
                            "географическом порядке. Если одна из точек "
                            "слишком далеко, замени её похожим местом "
                            "ближе к остальным активностям этого дня."
                        )

                        if st.button(
                            f"✨ Подготовить AI-команду для дня {day_number}",
                            key=(
                                f"optimize_logistics_"
                                f"{trip_id}_{day_number}"
                            ),
                            use_container_width=True,
                        ):
                            st.session_state[
                                f"ai_edit_request_{trip_id}"
                            ] = logistics_request

                            st.success(
                                "Команда подготовлена. Откройте вкладку "
                                "«💬 Изменить с AI», при необходимости "
                                "отредактируйте текст и нажмите "
                                "«✦ Обновить маршрут с AI»."
                            )



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

    remaining_budget = total_cost - actual_sum

    if total_cost > 0:
        budget_percent = (actual_sum / total_cost) * 100
    else:
        budget_percent = 0

    progress_width = min(max(budget_percent, 0), 100)

    if actual_sum <= 0:
        progress_color = "#8B5CF6"
        progress_text = "Фактические расходы пока не внесены"
        remaining_class = ""
    elif budget_percent < 75:
        progress_color = "#22D3EE"
        progress_text = f"Использовано {budget_percent:.0f}% бюджета"
        remaining_class = "is-positive"
    elif budget_percent <= 100:
        progress_color = "#FBBF24"
        progress_text = (
            f"Использовано {budget_percent:.0f}% бюджета — "
            "контролируйте оставшиеся расходы"
        )
        remaining_class = "is-warning"
    else:
        progress_color = "#FB7185"
        progress_text = (
            "Бюджет превышен на "
            f"{format_money(abs(remaining_budget), curr)}"
        )
        remaining_class = "is-danger"

    if remaining_budget >= 0:
        remaining_text = format_money(remaining_budget, curr)
    else:
        remaining_text = f"−{format_money(abs(remaining_budget), curr)}"

    st.markdown(
        (
            '<div class="tm-budget-summary">'
            '<div class="tm-budget-summary-label">Бюджет поездки</div>'
            '<div class="tm-budget-summary-total">'
            f'{format_money(total_cost, curr)}'
            '</div>'
            '<div class="tm-budget-summary-caption">'
            'Контролируйте плановые и фактические расходы в одном месте.'
            '</div>'
            '<div class="tm-budget-summary-grid">'
            '<div class="tm-budget-summary-item">'
            '<div class="tm-budget-summary-item-label">План</div>'
            '<div class="tm-budget-summary-item-value">'
            f'{format_money(plan_sum, curr)}'
            '</div>'
            '</div>'
            '<div class="tm-budget-summary-item">'
            '<div class="tm-budget-summary-item-label">По факту</div>'
            '<div class="tm-budget-summary-item-value">'
            f'{format_money(actual_sum, curr)}'
            '</div>'
            '</div>'
            '<div class="tm-budget-summary-item">'
            '<div class="tm-budget-summary-item-label">Остаток</div>'
            f'<div class="tm-budget-summary-item-value {remaining_class}">'
            f'{remaining_text}'
            '</div>'
            '</div>'
            '</div>'
            '<div class="tm-budget-progress-track">'
            '<div class="tm-budget-progress-value" '
            f'style="width:{progress_width:.1f}%;'
            f'background:{progress_color};'
            f'color:{progress_color};"></div>'
            '</div>'
            '<div class="tm-budget-progress-text">'
            f'{progress_text}'
            '</div>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )
    # ======================================================
    # AI-АНАЛИЗ БЮДЖЕТА
    # ======================================================

    st.markdown(
        '<div class="tm-section-title">✨ AI-анализ бюджета</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        (
            '<div class="tm-section-text">'
            'TravelMind проанализирует плановые, фактические и '
            'внеплановые расходы и предложит способы держать бюджет '
            'под контролем.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    category_labels_for_ai = {
        "A": "Активности",
        "F": "Еда",
        "T": "Транспорт",
        "S": "Проживание",
        "L": "Отдых и прогулки",
        "H": "Покупки",
        "W": "Прочее",
    }

    category_summary = {}

    for expense in expenses:
        category_code = text_value(expense["category"], "W")
        category_name = category_labels_for_ai.get(
            category_code,
            "Прочее",
        )

        if category_name not in category_summary:
            category_summary[category_name] = {
                "planned": 0.0,
                "actual": 0.0,
                "manual_actual": 0.0,
            }

        category_summary[category_name]["planned"] += as_float(
            expense["cost_plan"]
        )
        category_summary[category_name]["actual"] += as_float(
            expense["cost_actual"]
        )

        if int(expense["is_manual"] or 0) == 1:
            category_summary[category_name]["manual_actual"] += as_float(
                expense["cost_actual"]
            )

    category_summary_for_ai = []

    for category_name, values in category_summary.items():
        category_summary_for_ai.append(
            {
                "category": category_name,
                "planned": round(values["planned"], 2),
                "actual": round(values["actual"], 2),
                "difference": round(
                    values["actual"] - values["planned"],
                    2,
                ),
                "unplanned_actual": round(
                    values["manual_actual"],
                    2,
                ),
            }
        )

    category_summary_for_ai.sort(
        key=lambda item: item["actual"],
        reverse=True,
    )

    manual_expenses_for_ai = [
        expense
        for expense in expenses
        if int(expense["is_manual"] or 0) == 1
    ]

    manual_actual_sum = sum(
        as_float(expense["cost_actual"])
        for expense in manual_expenses_for_ai
    )

    days_count = max(len(data.get("days", [])), 1)

    budget_ai_context = {
        "destination": destination,
        "currency": curr,
        "trip_days": days_count,
        "total_budget": round(total_cost, 2),
        "planned_total": round(plan_sum, 2),
        "actual_total": round(actual_sum, 2),
        "remaining_budget": round(remaining_budget, 2),
        "budget_used_percent": round(budget_percent, 1),
        "unplanned_expenses_count": len(manual_expenses_for_ai),
        "unplanned_actual_total": round(manual_actual_sum, 2),
        "categories": category_summary_for_ai,
    }

    budget_ai_state_key = f"budget_ai_analysis_{trip_id}"

    if st.button(
        "✨ Получить рекомендации AI",
        key=f"run_budget_ai_analysis_{trip_id}",
        use_container_width=True,
    ):
        with st.spinner(
            "TravelMind анализирует расходы и готовит рекомендации…"
        ):
            try:
                analysis_result = ai.analyze_budget_with_ai(
                    budget_ai_context
                )

                st.session_state[budget_ai_state_key] = {
                    "data": analysis_result["data"],
                    "generated_at": datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    "tokens_in": analysis_result["tokens_in"],
                    "tokens_out": analysis_result["tokens_out"],
                }

                st.rerun()

            except json.JSONDecodeError as error:
                st.error(
                    "AI вернул ответ в неверном формате. "
                    "Попробуйте запросить анализ ещё раз."
                )
                st.caption(f"Техническая информация: {str(error)[:1000]}")

            except Exception as error:
                st.error("Не удалось выполнить AI-анализ бюджета.")
                st.caption(f"Техническая информация: {str(error)[:1000]}")

            except Exception as error:
                st.error(
                    "Не удалось выполнить AI-анализ бюджета: "
                    f"{error}"
                )

    saved_budget_analysis = st.session_state.get(budget_ai_state_key)

    if saved_budget_analysis:
        analysis_data = saved_budget_analysis.get("data") or {}
        analysis_status = text_value(analysis_data.get("status"))
        analysis_summary = text_value(
            analysis_data.get("summary"),
            "AI подготовил рекомендации по бюджету.",
        )
        recommendations = analysis_data.get("recommendations") or []

        status_config = {
            "safe": {
                "icon": "🟢",
                "title": "Бюджет под контролем",
            },
            "attention": {
                "icon": "🟡",
                "title": "Стоит обратить внимание",
            },
            "over_budget": {
                "icon": "🔴",
                "title": "Есть риск превышения бюджета",
            },
            "no_data": {
                "icon": "🔵",
                "title": "Недостаточно фактических данных",
            },
        }

        current_status = status_config.get(
            analysis_status,
            {
                "icon": "✨",
                "title": "Рекомендации TravelMind AI",
            },
        )

        with st.container(border=True):
            st.markdown(
                (
                    f"### {current_status['icon']} "
                    f"{current_status['title']}"
                )
            )

            st.write(analysis_summary)

            if recommendations:
                st.markdown("##### Что можно сделать")

                priority_icons = {
                    "low": "🟢",
                    "medium": "🟡",
                    "high": "🔴",
                }

                for recommendation in recommendations[:4]:
                    priority = text_value(
                        recommendation.get("priority"),
                        "low",
                    )
                    recommendation_title = text_value(
                        recommendation.get("title"),
                        "Рекомендация",
                    )
                    recommendation_text = text_value(
                        recommendation.get("text"),
                    )

                    st.markdown(
                        (
                            f"{priority_icons.get(priority, '✨')} "
                            f"**{recommendation_title}**  \n"
                            f"{recommendation_text}"
                        )
                    )

            saving_min = as_float(
                analysis_data.get("potential_saving_min")
            )
            saving_max = as_float(
                analysis_data.get("potential_saving_max")
            )

            if saving_min > 0 or saving_max > 0:
                if saving_max < saving_min:
                    saving_min, saving_max = saving_max, saving_min

                if saving_min == saving_max:
                    saving_text = format_money(saving_min, curr)
                else:
                    saving_text = (
                        f"{format_money(saving_min, curr)} — "
                        f"{format_money(saving_max, curr)}"
                    )

                st.success(
                    "Оценка потенциальной экономии: "
                    f"{saving_text}."
                )

            generated_at = text_value(
                saved_budget_analysis.get("generated_at")
            )

            if generated_at:
                st.caption(
                    "Анализ сформирован: "
                    f"{generated_at}. "
                    "После изменения расходов нажмите кнопку "
                    "ещё раз, чтобы обновить рекомендации."
                )

            st.caption(
                "ℹ️ AI-рекомендации являются ориентировочными и не "
                "заменяют проверку актуальных цен."
            )
    max_trip_day = max(
        len(data.get("days", [])),
        max(
            (
                int(item["day"])
                for item in expenses
                if item["day"] is not None
            ),
            default=1,
        ),
    )

    category_options = {
        "🏛️ Активности": "A",
        "🍽️ Еда": "F",
        "🚌 Транспорт": "T",
        "🏨 Проживание": "S",
        "🌿 Отдых и прогулки": "L",
        "🛍️ Покупки": "H",
        "✨ Прочее": "W",
    }

    expense_category_labels = {
        "A": "🏛️ Активности",
        "F": "🍽️ Еда",
        "T": "🚌 Транспорт",
        "S": "🏨 Проживание",
        "L": "🌿 Отдых и прогулки",
        "H": "🛍️ Покупки",
        "W": "✨ Прочее",
    }

    st.markdown(
        '<div style="height: 0.45rem;"></div>',
        unsafe_allow_html=True,
    )

    tab_all_expenses, tab_manual_expenses = st.tabs(
        [
            "◫ Все расходы маршрута",
            "✦ Внеплановые расходы",
        ]
    )

    # ======================================================
    # ВНУТРЕННЯЯ ВКЛАДКА: ВСЕ РАСХОДЫ
    # ======================================================

    with tab_all_expenses:
        st.markdown(
            (
                '<div class="tm-section-text">'
                'Здесь отображаются плановые позиции AI-маршрута и '
                'добавленные вручную расходы. Используйте фильтры, '
                'чтобы быстро найти нужную трату.'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        available_days = sorted(
            {
                int(item["day"])
                for item in expenses
                if item["day"] is not None
            }
        )

        available_categories = sorted(
            {
                text_value(item["category"])
                for item in expenses
                if item["category"]
            }
        )

        filter_col_1, filter_col_2, filter_col_3 = st.columns(
            [1.1, 1.45, 1.45],
        )

        with filter_col_1:
            selected_day = st.selectbox(
                "День",
                options=["Все дни"] + available_days,
                key=f"expense_filter_day_{trip_id}",
            )

        with filter_col_2:
            selected_category = st.selectbox(
                "Категория",
                options=["Все категории"] + available_categories,
                format_func=lambda value: (
                    value
                    if value == "Все категории"
                    else expense_category_labels.get(value, value)
                ),
                key=f"expense_filter_category_{trip_id}",
            )

        with filter_col_3:
            only_without_actual = st.checkbox(
                "Только без факта",
                value=False,
                key=f"expense_filter_without_actual_{trip_id}",
                help=(
                    "Показывает расходы, для которых фактическая "
                    "сумма ещё не внесена."
                ),
            )

        filtered_expenses = []

        for item in expenses:
            item_day = item["day"]
            item_category = text_value(item["category"])
            item_actual = item["cost_actual"]

            if selected_day != "Все дни" and item_day != selected_day:
                continue

            if (
                selected_category != "Все категории"
                and item_category != selected_category
            ):
                continue

            if only_without_actual and as_float(item_actual) > 0:
                continue

            filtered_expenses.append(item)

        if not filtered_expenses:
            st.info(
                "По выбранным фильтрам расходов не найдено. "
                "Измените условия фильтрации."
            )

        for expense in filtered_expenses:
            expense_id = expense["id"]
            day_number = expense["day"]
            category = text_value(expense["category"])
            title = text_value(expense["title"])
            plan_cost = as_float(expense["cost_plan"])
            actual_cost = as_float(expense["cost_actual"])

            difference = actual_cost - plan_cost

            if actual_cost == 0:
                status_text = "○ Факт пока не внесён"
                status_class = ""
            elif abs(difference) < 0.01:
                status_text = "✓ Совпадает с планом"
                status_class = ""
            elif difference < 0:
                status_text = (
                    f"↓ Экономия: {format_money(abs(difference), curr)}"
                )
                status_class = "is-saving"
            else:
                status_text = (
                    f"↑ Превышение: {format_money(difference, curr)}"
                )
                status_class = "is-over"

            with st.container(border=True):
                st.markdown(
                    (
                        '<div class="tm-expense-heading">'
                        '<div class="tm-expense-title">'
                        f'{ICONS.get(category, "📍")} {escape(title)}'
                        '</div>'
                        '<div class="tm-expense-day">'
                        f'День {escape(str(day_number))}'
                        '</div>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )

                plan_column, fact_column, save_column = st.columns(
                    [1.25, 2.2, 0.95],
                )

                with plan_column:
                    st.markdown(
                        '<div class="tm-expense-label">План</div>',
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        (
                            '<div class="tm-expense-plan-value">'
                            f'{format_money(plan_cost, curr)}'
                            '</div>'
                        ),
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        (
                            f'<div class="tm-expense-status {status_class}">'
                            f'{status_text}'
                            '</div>'
                        ),
                        unsafe_allow_html=True,
                    )

                with fact_column:
                    st.markdown(
                        (
                            '<div class="tm-expense-fact-label">'
                            'Фактический расход'
                            '</div>'
                        ),
                        unsafe_allow_html=True,
                    )

                    actual_value = st.number_input(
                        "Фактический расход",
                        min_value=0.0,
                        max_value=10000000.0,
                        value=float(actual_cost),
                        step=10.0,
                        format="%.2f",
                        key=f"actual_{expense_id}",
                        label_visibility="collapsed",
                    )

                with save_column:
                    st.markdown(
                        '<div class="tm-expense-label">Действие</div>',
                        unsafe_allow_html=True,
                    )

                    if st.button(
                        "💾 Сохранить",
                        key=f"save_{expense_id}",
                        use_container_width=True,
                    ):
                        db.update_expense_actual(
                            expense_id,
                            float(actual_value),
                        )
                        st.toast("Расход сохранён.")
                        st.rerun()

                    st.markdown(
                        (
                            '<div class="tm-expense-save-note">'
                            'Сумма сохранится в фактических расходах.'
                            '</div>'
                        ),
                        unsafe_allow_html=True,
                    )

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
                            alt.Tooltip(
                                "Категория:N",
                                title="Категория",
                            ),
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

    # ======================================================
    # ВНУТРЕННЯЯ ВКЛАДКА: РУЧНЫЕ РАСХОДЫ
    # ======================================================

    with tab_manual_expenses:
        st.markdown(
            (
                '<div class="tm-section-text">'
                'Добавляйте расходы, которых не было в первоначальном '
                'маршруте: такси, кофе, сувениры, билеты, покупки '
                'и другие внеплановые траты. Каждый расход можно '
                'изменить или удалить.'
                '</div>'
            ),
            unsafe_allow_html=True,
        )

        manual_form_state_key = f"manual_expense_form_open_{trip_id}"

        if manual_form_state_key not in st.session_state:
            st.session_state[manual_form_state_key] = False

        if not st.session_state[manual_form_state_key]:
            if st.button(
                "＋ Добавить расход вручную",
                key=f"open_manual_expense_form_{trip_id}",
                use_container_width=True,
            ):
                st.session_state[manual_form_state_key] = True
                st.rerun()

        else:
            st.markdown(
                '<div class="tm-section-title">＋ Новый ручной расход</div>',
                unsafe_allow_html=True,
            )

            with st.form(
                f"manual_expense_form_{trip_id}",
                clear_on_submit=True,
            ):
                manual_title = st.text_input(
                    "Название расхода",
                    placeholder="Например: Такси из аэропорта",
                    key=f"manual_expense_title_{trip_id}",
                )

                manual_col_1, manual_col_2 = st.columns(2)

                with manual_col_1:
                    manual_category_label = st.selectbox(
                        "Категория",
                        options=list(category_options.keys()),
                        key=f"manual_expense_category_{trip_id}",
                    )

                    manual_day = st.selectbox(
                        "День поездки",
                        options=list(range(1, max_trip_day + 1)),
                        key=f"manual_expense_day_{trip_id}",
                    )

                with manual_col_2:
                    manual_plan = st.number_input(
                        "Плановая сумма",
                        min_value=0.0,
                        max_value=10000000.0,
                        value=0.0,
                        step=100.0,
                        format="%.2f",
                        key=f"manual_expense_plan_{trip_id}",
                    )

                    manual_actual = st.number_input(
                        "Фактическая сумма",
                        min_value=0.0,
                        max_value=10000000.0,
                        value=0.0,
                        step=100.0,
                        format="%.2f",
                        key=f"manual_expense_actual_{trip_id}",
                    )

                save_col, cancel_col = st.columns(2)

                with save_col:
                    manual_submitted = st.form_submit_button(
                        "✓ Добавить расход",
                        use_container_width=True,
                    )

                with cancel_col:
                    manual_cancelled = st.form_submit_button(
                        "Отмена",
                        use_container_width=True,
                    )

            if manual_cancelled:
                st.session_state[manual_form_state_key] = False
                st.rerun()

            if manual_submitted:
                if not manual_title.strip():
                    st.warning("Введите название расхода.")
                elif manual_actual <= 0:
                    st.warning("Укажите фактическую сумму расхода.")
                else:
                    try:
                        db.add_manual_expense(
                            trip_id=trip_id,
                            user_id=user_id,
                            day=int(manual_day),
                            category=category_options[
                                manual_category_label
                            ],
                            title=manual_title,
                            cost_plan=float(manual_plan),
                            cost_actual=float(manual_actual),
                        )

                        st.session_state[manual_form_state_key] = False
                        st.toast("Ручной расход добавлен.")
                        st.rerun()

                    except ValueError as error:
                        st.error(str(error))

        manual_expenses = db.get_manual_expenses(trip_id)

        if not manual_expenses:
            st.info(
                "Ручных расходов пока нет. Добавьте первую трату "
                "с помощью кнопки выше."
            )

        for manual_expense in manual_expenses:
            manual_expense_id = manual_expense["id"]
            manual_category = text_value(manual_expense["category"])
            manual_title_text = text_value(
                manual_expense["title"],
                "Расход без названия",
            )
            manual_day_number = int(manual_expense["day"] or 1)
            manual_plan_cost = as_float(manual_expense["cost_plan"])
            manual_actual_cost = as_float(
                manual_expense["cost_actual"]
            )

            plan_text = ""

            if manual_plan_cost > 0:
                plan_text = (
                    '<div class="tm-manual-expense-plan">'
                    f'План: {format_money(manual_plan_cost, curr)}'
                    '</div>'
                )

            st.markdown(
                (
                    '<div class="tm-manual-expense-card">'
                    '<div class="tm-manual-expense-main">'
                    '<div class="tm-manual-expense-title">'
                    f'{ICONS.get(manual_category, "✨")} '
                    f'{escape(manual_title_text)}'
                    '</div>'
                    '<div class="tm-manual-expense-meta">'
                    f'Добавлено вручную · День {manual_day_number}'
                    '</div>'
                    f'{plan_text}'
                    '</div>'
                    '<div class="tm-manual-expense-amount">'
                    f'{format_money(manual_actual_cost, curr)}'
                    '<div class="tm-manual-expense-plan">'
                    'Фактический расход'
                    '</div>'
                    '</div>'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

            edit_form_state_key = (
                f"edit_manual_expense_open_{manual_expense_id}"
            )

            if edit_form_state_key not in st.session_state:
                st.session_state[edit_form_state_key] = False

            action_col_1, action_col_2 = st.columns(2)

            with action_col_1:
                if st.button(
                    "✏️ Изменить расход",
                    key=f"open_edit_manual_expense_{manual_expense_id}",
                    use_container_width=True,
                ):
                    st.session_state[edit_form_state_key] = True
                    st.rerun()

            with action_col_2:
                if st.button(
                    "🗑️ Удалить расход",
                    key=f"delete_manual_expense_{manual_expense_id}",
                    use_container_width=True,
                ):
                    try:
                        db.delete_manual_expense(
                            expense_id=manual_expense_id,
                            trip_id=trip_id,
                            user_id=user_id,
                        )
                        st.toast("Ручной расход удалён.")
                        st.rerun()

                    except ValueError as error:
                        st.error(str(error))

            if st.session_state[edit_form_state_key]:
                with st.form(
                    f"edit_manual_expense_form_{manual_expense_id}",
                ):
                    st.markdown("##### Редактирование ручного расхода")

                    edit_title = st.text_input(
                        "Название расхода",
                        value=manual_title_text,
                        key=f"edit_manual_title_{manual_expense_id}",
                    )

                    edit_col_1, edit_col_2 = st.columns(2)

                    category_labels = list(category_options.keys())
                    category_values = list(category_options.values())

                    try:
                        category_index = category_values.index(
                            manual_category
                        )
                    except ValueError:
                        category_index = 0

                    with edit_col_1:
                        edit_category_label = st.selectbox(
                            "Категория",
                            options=category_labels,
                            index=category_index,
                            key=f"edit_manual_category_{manual_expense_id}",
                        )

                        edit_day = st.selectbox(
                            "День поездки",
                            options=list(range(1, max_trip_day + 1)),
                            index=min(
                                max(manual_day_number - 1, 0),
                                max_trip_day - 1,
                            ),
                            key=f"edit_manual_day_{manual_expense_id}",
                        )

                    with edit_col_2:
                        edit_plan = st.number_input(
                            "Плановая сумма",
                            min_value=0.0,
                            max_value=10000000.0,
                            value=float(manual_plan_cost),
                            step=100.0,
                            format="%.2f",
                            key=f"edit_manual_plan_{manual_expense_id}",
                        )

                        edit_actual = st.number_input(
                            "Фактическая сумма",
                            min_value=0.0,
                            max_value=10000000.0,
                            value=float(manual_actual_cost),
                            step=100.0,
                            format="%.2f",
                            key=f"edit_manual_actual_{manual_expense_id}",
                        )

                    form_save_col, form_cancel_col = st.columns(2)

                    with form_save_col:
                        edit_submitted = st.form_submit_button(
                            "✓ Сохранить изменения",
                            use_container_width=True,
                        )

                    with form_cancel_col:
                        edit_cancelled = st.form_submit_button(
                            "Отмена",
                            use_container_width=True,
                        )

                if edit_cancelled:
                    st.session_state[edit_form_state_key] = False
                    st.rerun()

                if edit_submitted:
                    if not edit_title.strip():
                        st.warning("Введите название расхода.")
                    elif edit_actual <= 0:
                        st.warning("Укажите фактическую сумму расхода.")
                    else:
                        try:
                            db.update_manual_expense(
                                expense_id=manual_expense_id,
                                trip_id=trip_id,
                                user_id=user_id,
                                day=int(edit_day),
                                category=category_options[
                                    edit_category_label
                                ],
                                title=edit_title,
                                cost_plan=float(edit_plan),
                                cost_actual=float(edit_actual),
                            )

                            st.session_state[edit_form_state_key] = False
                            st.toast("Ручной расход обновлён.")
                            st.rerun()

                        except ValueError as error:
                            st.error(str(error))
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
# ВКЛАДКА: ИЗМЕНИТЬ С AI
# ==========================================================

with tab_edit:
    st.markdown(
        """
        <div class="tm-ai-edit-card">
            <div class="tm-ai-edit-title">💬 Изменить маршрут с AI</div>
            <div class="tm-ai-edit-text">
                Напишите, что нужно изменить. TravelMind проанализирует
                текущий маршрут, обновит активности, бюджет, советы
                и сохранит новую версию поездки.
            </div>
            <div class="tm-ai-edit-warning">
                ℹ️ Плановые расходы будут пересчитаны. Внесённые фактические
                расходы сохраняются, если активность останется в маршруте
                с тем же названием.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="height: 1rem;"></div>',
        unsafe_allow_html=True,
    )

    st.markdown("##### Быстрые команды")

    preset_col_1, preset_col_2, preset_col_3 = st.columns(3)
    preset_col_4, preset_col_5, preset_col_6 = st.columns(3)

    edit_request_key = f"ai_edit_request_{trip_id}"

    if edit_request_key not in st.session_state:
        st.session_state[edit_request_key] = ""

    with preset_col_1:
        if st.button(
            "💸 Сделать дешевле",
            key=f"edit_cheaper_{trip_id}",
            use_container_width=True,
        ):
            st.session_state[edit_request_key] = (
                "Сделай маршрут дешевле примерно на 20%, "
                "но сохрани главные впечатления поездки."
            )
            st.rerun()

    with preset_col_2:
        if st.button(
            "🌿 Сделать спокойнее",
            key=f"edit_slower_{trip_id}",
            use_container_width=True,
        ):
            st.session_state[edit_request_key] = (
                "Сделай маршрут более спокойным: не более 2–3 "
                "основных активностей в день, добавь время на отдых."
            )
            st.rerun()

    with preset_col_3:
        if st.button(
            "🏛️ Больше культуры",
            key=f"edit_culture_{trip_id}",
            use_container_width=True,
        ):
            st.session_state[edit_request_key] = (
                "Добавь больше музеев, истории, архитектуры "
                "и культурных впечатлений."
            )
            st.rerun()

    with preset_col_4:
        if st.button(
            "🍽️ Больше гастрономии",
            key=f"edit_food_{trip_id}",
            use_container_width=True,
        ):
            st.session_state[edit_request_key] = (
                "Добавь больше локальной кухни, интересных кафе, "
                "рынков и гастрономических впечатлений."
            )
            st.rerun()

    with preset_col_5:
        if st.button(
            "👨‍👩‍👧 Для семьи",
            key=f"edit_family_{trip_id}",
            use_container_width=True,
        ):
            st.session_state[edit_request_key] = (
                "Адаптируй маршрут для семьи с ребёнком: "
                "сделай темп комфортным, логистику простой, "
                "добавь подходящие семейные активности."
            )
            st.rerun()

    with preset_col_6:
        if st.button(
            "✨ Необычные места",
            key=f"edit_unusual_{trip_id}",
            use_container_width=True,
        ):
            st.session_state[edit_request_key] = (
                "Добавь необычные, атмосферные и нетипичные места, "
                "которые подходят выбранному направлению."
            )
            st.rerun()

    st.markdown(
        '<div style="height: 0.65rem;"></div>',
        unsafe_allow_html=True,
    )

    with st.form(f"ai_edit_form_{trip_id}"):
        edit_request = st.text_area(
            "Что изменить в маршруте?",
            key=edit_request_key,
            placeholder=(
                "Например: убери длительные прогулки, добавь день "
                "для шопинга и замени дорогие рестораны на локальные кафе."
            ),
            height=130,
        )

        edit_submitted = st.form_submit_button(
            "✦ Обновить маршрут с AI",
            use_container_width=True,
        )

    if edit_submitted:
        clean_request = edit_request.strip()

        if not clean_request:
            st.warning("Напишите, что нужно изменить в маршруте.")
        else:
            with st.spinner(
                "✦ AI обновляет маршрут, бюджет и рекомендации… "
                "обычно это занимает 20–60 секунд."
            ):
                try:
                    edit_result = ai.edit_trip_with_ai(
                        current_data=data,
                        trip_context=dict(trip),
                        user_request=clean_request,
                    )

                    updated_data = edit_result["data"]
                    validation_errors = ai.validate(updated_data)

                    if validation_errors:
                        st.error(
                            "AI вернул маршрут с неполной структурой. "
                            "Изменения не были сохранены."
                        )

                        for validation_error in validation_errors:
                            st.warning(validation_error)

                    else:
                        edit_history = data.get("_ai_edit_history") or []

                        edit_history.append(
                            {
                                "request": clean_request,
                                "edited_at": datetime.now().strftime(
                                    "%d/%m/%Y %H:%M"
                                ),
                                "tokens_in": edit_result.get(
                                    "tokens_in",
                                    0,
                                ),
                                "tokens_out": edit_result.get(
                                    "tokens_out",
                                    0,
                                ),
                            }
                        )

                        updated_data["_ai_edit_history"] = edit_history[-10:]

                        db.update_trip_from_ai(
                            trip_id=trip_id,
                            user_id=user_id,
                            updated_data=updated_data,
                        )

                        st.session_state.pop(edit_request_key, None)

                        st.toast("Маршрут успешно обновлён с помощью AI.")
                        st.rerun()

                except json.JSONDecodeError:
                    st.error(
                        "AI вернул некорректный JSON. "
                        "Маршрут не был изменён — попробуйте ещё раз."
                    )

                except Exception as error:
                    st.error(
                        "Не удалось обновить маршрут через AI: "
                        f"{error}"
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
