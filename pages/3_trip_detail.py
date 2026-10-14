"""Детали поездки: план по дням, карта, план/факт расходов, советы, экспорт."""
import json
from collections import defaultdict

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import ai
import auth
import db

st.set_page_config(page_title="Детали поездки", page_icon="🗺", layout="wide")

user_id = auth.require_auth()

trip_id = st.session_state.get("current_trip_id")
if not trip_id:
    st.warning("Поездка не выбрана. Откройте её из списка.")
    st.page_link("pages/2_my_trips.py", label="К списку поездок →")
    st.stop()

trip = db.get_trip(trip_id, user_id)
if not trip:
    st.error("Поездка не найдена или удалена.")
    st.page_link("pages/2_my_trips.py", label="К списку поездок →")
    st.stop()

data = json.loads(trip["data"])
curr = trip["currency"]

ICONS = {"A": "🏛", "F": "🍽", "T": "🚌", "S": "🏨",
         "L": "🌿", "H": "🛍", "W": "✨"}
COLORS = {"A": "blue", "F": "orange", "T": "gray", "S": "purple",
          "L": "green", "H": "pink", "W": "red"}
BUDGET_RU = {"accommodation": "Проживание", "food": "Еда",
             "activities": "Активности", "transport": "Транспорт",
             "other": "Прочее"}
TIP_RU = {"transport": "🚌 Транспорт", "safety": "🛡 Безопасность",
          "culture": "🎭 Культура", "money": "💵 Деньги"}

# ---------- Шапка и метрики ----------
st.title(data.get("title", trip["title"]))
st.caption(
    f"{trip['destination']} · {trip['start_date']} — {trip['end_date']} · "
    f"{trip['people']} чел. · промпт {ai.PROMPT_VERSION}"
)
st.write(data.get("overview", ""))

expenses = db.get_expenses(trip_id)
plan_sum = sum((e["cost_plan"] or 0) for e in expenses)
actual_sum = sum((e["cost_actual"] or 0) for e in expenses)

m1, m2, m3, m4 = st.columns(4)
m1.metric("План", f"{data.get('total_cost') or plan_sum:.0f} {curr}")
m2.metric(
    "Факт",
    f"{actual_sum:.0f} {curr}",
    delta=(f"{actual_sum - plan_sum:+.0f} {curr}" if actual_sum else None),
)
m3.metric("Mood", f"{data.get('mood_score', '—')}/10")
m4.metric("Дней", len(data.get("days", [])))

if data.get("mood_reason"):
    st.caption(f"🙂 {data['mood_reason']}")

tabs = st.tabs(["📅 План", "🗺 Карта", "💰 План/факт", "✨ Фишки", "🔧 JSON"])

# ---------- Вкладка 1: план по дням ----------
with tabs[0]:
    acc = data.get("accommodation") or {}
    if acc:
        st.info(
            f"🏨 **Проживание:** {acc.get('type', '')} в районе "
            f"{acc.get('area', '')} · ~{acc.get('price_per_night', 0)} "
            f"{curr}/ночь. {acc.get('why', '')}"
        )

    for d in data.get("days", []):
        header = (
            f"День {d.get('day')} · {d.get('date', '')} — {d.get('theme', '')}"
            f"  ·  {d.get('vibe', '')}"
        )
        with st.expander(header, expanded=(d.get("day") == 1)):
            for a in d.get("activities", []):
                icon = ICONS.get(a.get("type"), "📍")
                st.markdown(
                    f"**{a.get('time', '')}** {icon} **{a.get('title', '')}** · "
                    f"{a.get('duration_min', '?')} мин · ~{a.get('cost', 0)} {curr}  \n"
                    f"📍 {a.get('location', '')}  \n"
                    f"{a.get('description', '')}"
                )
                if a.get("tip"):
                    st.caption(f"💡 {a['tip']}")
            st.markdown(f"**Итого за день:** ~{d.get('day_cost', 0)} {curr}")

# ---------- Вкладка 2: карта ----------
with tabs[1]:
    points = []
    for d in data.get("days", []):
        for a in d.get("activities", []):
            lat, lon = a.get("lat"), a.get("lon")
            if isinstance(lat, (int, float)) and isinstance(lon, (int, float)):
                points.append((lat, lon, a, d.get("day")))

    if not points:
        st.info("Для этой поездки модель не вернула координаты.")
    else:
        center = [
            sum(p[0] for p in points) / len(points),
            sum(p[1] for p in points) / len(points),
        ]
        fmap = folium.Map(
            location=center,
            zoom_start=12,
            tiles="CartoDB dark_matter",
            attr="© OpenStreetMap contributors © CARTO",
        )

        for lat, lon, a, day in points:
            folium.Marker(
                [lat, lon],
                popup=(
                    f"День {day} · {a.get('time', '')}<br>"
                    f"<b>{a.get('title', '')}</b><br>{a.get('location', '')}"
                ),
                tooltip=a.get("title", ""),
                icon=folium.Icon(
                    color=COLORS.get(a.get("type"), "blue"),
                    icon="info-sign",
                ),
            ).add_to(fmap)

        by_day = defaultdict(list)
        for lat, lon, _, day in points:
            by_day[day].append([lat, lon])
        for pts in by_day.values():
            if len(pts) > 1:
                folium.PolyLine(pts, weight=3, opacity=0.6).add_to(fmap)

        st_folium(fmap, use_container_width=True, height=520,
                  returned_objects=[])

# ---------- Вкладка 3: план / факт ----------
with tabs[2]:
    st.caption("Вносите фактические суммы — отклонение считается автоматически.")

    for e in expenses:
        c1, c2, c3, c4 = st.columns([4, 1, 2, 1])
        c1.text(f"Д{e['day']} · {ICONS.get(e['category'], '•')} {e['title']}")
        c2.text(f"план: {(e['cost_plan'] or 0):.0f}")
        actual_val = c3.number_input(
            "Факт",
            min_value=0.0,
            value=float(e["cost_actual"] or 0),
            step=10.0,
            key=f"act_{e['id']}",
            label_visibility="collapsed",
        )
        if c4.button("💾", key=f"save_{e['id']}"):
            db.update_expense_actual(e["id"], actual_val)
            st.toast("Сохранено")
            st.rerun()

    bd = data.get("budget_breakdown") or {}
    if bd:
        df = pd.DataFrame({
            "Категория": [BUDGET_RU.get(k, k) for k in bd],
            "План": pd.to_numeric(list(bd.values()), errors="coerce"),
        }).fillna(0).set_index("Категория")
        st.bar_chart(df)
        st.dataframe(df, use_container_width=True)
        st.caption(f"Сумма по категориям: {df['План'].sum():.0f} {curr}")
    else:
        st.info("Модель не вернула разбивку бюджета.")

# ---------- Вкладка 4: фишки ----------
with tabs[3]:
    wm = data.get("wow_moments") or []
    if wm:
        st.subheader("✨ Главные впечатления")
        for w in wm:
            st.markdown(f"- {w}")

    packing = data.get("packing") or []
    if packing:
        st.subheader("🎒 Что взять с собой")
        for i, p in enumerate(packing):
            st.checkbox(p, key=f"pack_{trip_id}_{i}")

    phrases = data.get("phrases") or []
    if phrases:
        st.subheader("💬 Полезные фразы")
        for ph in phrases:
            st.markdown(f"**{ph.get('ru', '')}** — _{ph.get('local', '')}_")

    tips = data.get("tips") or {}
    if tips:
        st.subheader("💡 Советы")
        for k, v in tips.items():
            st.markdown(f"- **{TIP_RU.get(k, k)}:** {v}")

# ---------- Вкладка 5: сырой JSON + экспорт ----------
with tabs[4]:
    st.json(data)
    d1, d2 = st.columns(2)
    d1.download_button(
        "⬇️ Скачать маршрут (Markdown)",
        ai.to_markdown(data, curr),
        file_name=f"travelmind_trip_{trip_id}.md",
    )
    d2.download_button(
        "⬇️ Скачать JSON",
        json.dumps(data, ensure_ascii=False, indent=2),
        file_name=f"travelmind_trip_{trip_id}.json",
    )
