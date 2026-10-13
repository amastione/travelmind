"""Страница создания поездки: форма параметров → генерация через LLM → запись в БД."""
import json
from datetime import date, timedelta

import streamlit as st

import ai
import auth
import db

st.set_page_config(page_title="Новая поездка", page_icon="📝", layout="wide")

# Защита страницы: без входа сюда не пустим
user_id = auth.require_auth()

st.title("📝 Новая поездка")
st.caption(f"Промпт {ai.PROMPT_VERSION} · модель {st.secrets.get('LLM_MODEL', 'deepseek-chat')}")

PACES = {"Спокойный": "slow", "Средний": "medium", "Насыщенный": "fast"}

with st.form("plan_form"):
    c1, c2 = st.columns(2)
    dest = c1.text_input("Куда едем?", placeholder="Стамбул, Турция")
    today = date.today()
    dates = c2.date_input(
        "Даты поездки",
        value=(today + timedelta(days=14), today + timedelta(days=17)),
        min_value=today,
    )

    c3, c4, c5 = st.columns(3)
    budget = c3.number_input("Бюджет", min_value=50, value=1000, step=50)
    curr = c4.selectbox("Валюта", ["USD", "EUR", "RUB"])
    people = c5.number_input("Человек", min_value=1, max_value=10, value=2)

    style = st.selectbox(
        "Стиль",
        ["Сбалансированный", "Бюджетный", "Комфорт / люкс", "Культурный",
         "Активный", "Гастрономический", "С детьми", "Романтический"],
    )
    pace = st.radio("Темп", list(PACES), index=1, horizontal=True)
    interests = st.multiselect(
        "Интересы",
        ["история", "музеи", "архитектура", "еда", "природа", "шопинг",
         "ночная жизнь", "фотография", "море", "горы", "спа", "спорт"],
        default=["история", "еда"],
    )
    notes = st.text_area(
        "Особые пожелания",
        placeholder="Без долгих пеших прогулок, вегетарианское питание…",
    )
    submitted = st.form_submit_button("✨ Сгенерировать маршрут")

if not submitted:
    st.info(
        f"Заполните форму слева. Максимум {ai.MAX_DAYS} дней — "
        "для учебного MVP этого достаточно."
    )
    st.stop()

# ---------- Валидация ввода ----------
if not dest.strip():
    st.error("Укажите направление поездки.")
    st.stop()

if not isinstance(dates, (list, tuple)) or len(dates) != 2:
    st.error("Выберите и дату начала, и дату окончания.")
    st.stop()

start, end = dates
days = (end - start).days + 1
if days < 1 or days > ai.MAX_DAYS:
    st.error(f"Поездка должна длиться от 1 до {ai.MAX_DAYS} дней.")
    st.stop()

# ---------- Сборка промпта ----------
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

# ---------- Генерация ----------
with st.spinner("Составляю маршрут… обычно 20–60 секунд"):
    try:
        result = ai.generate(user_prompt)
    except json.JSONDecodeError:
        st.error("Модель вернула некорректный JSON. Нажмите «Сгенерировать» ещё раз.")
        st.stop()
    except Exception as e:
        st.error(f"Ошибка обращения к модели: {e}")
        st.stop()

data = result["data"]

# ---------- Предупреждения по качеству ----------
for w in ai.validate(data):
    st.warning(w)

# ---------- Сохранение ----------
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

st.success(
    f"✅ Маршрут сохранён. Токены: {result['tokens_in']} вход / "
    f"{result['tokens_out']} выход."
)
st.session_state["current_trip_id"] = trip_id

if st.button("Открыть маршрут →", type="primary"):
    st.switch_page("pages/3_trip_detail.py")
