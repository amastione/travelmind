"""Детали поездки: маршрут, карта, расходы, советы и экспорт."""
import json
from collections import defaultdict
from datetime import date
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

# Проверяем, что пользователь авторизован
user_id = auth.require_auth()

# Получаем выбранную поездку из сессии
trip_id = st.session_state.get("current_trip_id")

if not trip_id:
    st.warning("Поездка не выбрана. Откройте её из списка поездок.")
    st.page_link("pages/2_my_trips.py", label="К списку поездок →")
    st.stop()

trip = db.get_trip(trip_id, user_id)

if not trip:
    st.error("Поездка не найдена или была удалена.")
    st.page_link("pages/2_my_trips.py", label="К списку поездок →")
    st.stop()

# Данные маршрута хранятся в базе в JSON
data = json.loads(trip["data"])
curr = trip["currency"]

# Словари для красивого отображения типов активностей
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
        "color": "#38bdf8",
        "emoji": "💎",
    },
    "Оптимальный": {
        "label": "ОПТИМАЛЬНЫЙ",
        "color": "#34d399",
        "emoji": "⭐",
    },
    "Премиум": {
        "label": "ПРЕМИУМ",
        "color": "#a78bfa",
        "emoji": "👑",
    },
}

# Тематические фото для учебного MVP:
# фасад, холл и интерьер номера.
HOTEL_IMAGES = {
    "Эконом": {
        "exterior": (
            "https://images.unsplash.com/"
            "photo-1566073771259-6a8506099945"
            "?auto=format&fit=crop&w=900&q=80"
        ),
        "lobby": (
            "https://images.unsplash.com/"
            "photo-1551882547-ff40c63fe5fa"
            "?auto=format&fit=crop&w=900&q=80"
        ),
        "room": (
            "https://images.unsplash.com/"
            "photo-1590490360182-c33d57733427"
            "?auto=format&fit=crop&w=900&q=80"
        ),
    },
    "Оптимальный": {
        "exterior": (
            "https://images.unsplash.com/"
            "photo-1542314831-068cd1dbfeeb"
            "?auto=format&fit=crop&w=900&q=80"
        ),
        "lobby": (
            "https://images.unsplash.com/"
            "photo-1600607687920-4e2a09cf159d"
            "?auto=format&fit=crop&w=900&q=80"
        ),
        "room": (
            "https://images.unsplash.com/"
            "photo-1618773928121-c32242e63f39"
            "?auto=format&fit=crop&w=900&q=80"
        ),
    },
    "Премиум": {
        "exterior": (
            "https://images.unsplash.com/"
            "photo-1571896349842-33c89424de2d"
            "?auto=format&fit=crop&w=900&q=80"
        ),
        "lobby": (
            "https://images.unsplash.com/"
            "photo-1582719508461-905c673771fd"
            "?auto=format&fit=crop&w=900&q=80"
        ),
        "room": (
            "https://images.unsplash.com/"
            "photo-1584132967334-10e028bd69f7"
            "?auto=format&fit=crop&w=900&q=80"
        ),
    },
}


# ---------- ШАПКА СТРАНИЦЫ ----------

st.title(data.get("title", trip["title"]))

st.caption(
    f"{trip['destination']} · "
    f"{trip['start_date']} — {trip['end_date']} · "
    f"{trip['people']} чел. · "
    f"Промпт {ai.PROMPT_VERSION}"
)

st.write(data.get("overview", ""))

expenses = db.get_expenses(trip_id)

plan_sum = sum((expense["cost_plan"] or 0) for expense in expenses)
actual_sum = sum((expense["cost_actual"] or 0) for expense in expenses)

total_cost = data.get("total_cost")
if not total_cost:
    total_cost = plan_sum

m1, m2, m3, m4 = st.columns(4)

m1.metric("Плановый бюджет", f"{total_cost:.0f} {curr}")

actual_delta = None
if actual_sum:
    actual_delta = f"{actual_sum - plan_sum:+.0f} {curr}"

m2.metric(
    "Фактические расходы",
    f"{actual_sum:.0f} {curr}",
    delta=actual_delta,
)

m3.metric("Ожидаемые эмоции", f"{data.get('mood_score', '—')}/10")
m4.metric("Дней в поездке", len(data.get("days", [])))

if data.get("mood_reason"):
    st.caption(f"🙂 {data['mood_reason']}")

tabs = st.tabs(
    [
        "📅 Маршрут по дням",
        "🗺️ Карта поездки",
        "💰 Бюджет и расходы",
        "✨ Советы путешественнику",
        "🔧 Данные AI",
    ]
)


# ---------- ВКЛАДКА 1. МАРШРУТ И ОТЕЛИ ----------

with tabs[0]:
    hotels = data.get("hotels") or []

    # Новый формат: три варианта отелей из AI-промпта v3.0
    if hotels:
        st.subheader("🏨 Где остановиться")

        st.caption(
            "Цены ориентировочные и указаны за один номер на одну ночь. "
            "Перед бронированием уточните стоимость, условия и наличие "
            "на официальном сайте отеля или в сервисе бронирования."
        )

        try:
            start_date = date.fromisoformat(str(trip["start_date"]))
            end_date = date.fromisoformat(str(trip["end_date"]))
            nights = max((end_date - start_date).days, 1)
        except (TypeError, ValueError):
            nights = max(len(data.get("days", [])) - 1, 1)

        hotel_columns = st.columns(3)

        for index, hotel in enumerate(hotels[:3]):
            tier = hotel.get("tier", "Оптимальный")

            style = TIER_STYLES.get(
                tier,
                TIER_STYLES["Оптимальный"],
            )

            images = HOTEL_IMAGES.get(
                tier,
                HOTEL_IMAGES["Оптимальный"],
            )

            rooms = hotel.get("rooms") or {}

            economy_price = float(rooms.get("economy", 0) or 0)
            standard_price = float(rooms.get("standard", 0) or 0)
            luxury_price = float(rooms.get("luxury", 0) or 0)

            total_stay = standard_price * nights

            with hotel_columns[index]:
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid {style["color"]};
                        border-radius: 16px;
                        padding: 12px 14px;
                        margin-bottom: 10px;
                        background: rgba(17, 24, 39, 0.55);
                    ">
                        <span style="
                            color: {style["color"]};
                            font-size: 12px;
                            font-weight: 700;
                            letter-spacing: 1px;
                        ">
                            {style["emoji"]} {style["label"]}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"#### {hotel.get('name', 'Вариант проживания')}"
                )

                st.caption(
                    f"📍 {hotel.get('area', 'Удобный район')}"
                )

                rating = hotel.get("rating", 0)

                try:
                    rating_value = float(rating)
                except (TypeError, ValueError):
                    rating_value = 0

                if rating_value > 0:
                    st.write(f"⭐ Рейтинг: **{rating_value:.1f}/10**")

                photo_1, photo_2, photo_3 = st.columns(3)

                with photo_1:
                    st.image(
                        images["exterior"],
                        use_container_width=True,
                    )
                    st.caption("Фасад")

                with photo_2:
                    st.image(
                        images["lobby"],
                        use_container_width=True,
                    )
                    st.caption("Холл")

                with photo_3:
                    st.image(
                        images["room"],
                        use_container_width=True,
                    )
                    st.caption("Номер")

                st.write(hotel.get("why", ""))

                st.markdown("**Ориентировочная цена за ночь**")

                price_col_1, price_col_2, price_col_3 = st.columns(3)

                price_col_1.metric(
                    "Эконом",
                    f"{economy_price:.0f} {curr}",
                )

                price_col_2.metric(
                    "Стандарт",
                    f"{standard_price:.0f} {curr}",
                )

                price_col_3.metric(
                    "Люкс",
                    f"{luxury_price:.0f} {curr}",
                )

                st.info(
                    f"Стандартный номер: примерно "
                    f"**{total_stay:.0f} {curr}** за {nights} ноч."
                )

                map_query = hotel.get(
                    "map_query",
                    f"{hotel.get('name', '')} {trip['destination']}",
                )

                google_maps_url = (
                    "https://www.google.com/maps/search/?api=1&query="
                    + quote_plus(map_query)
                )

                st.link_button(
                    "📍 Найти на карте",
                    google_maps_url,
                    use_container_width=True,
                )

        st.divider()

    # Поддержка старого поля accommodation для старых поездок
    accommodation = data.get("accommodation") or {}

    if not hotels and isinstance(accommodation, dict) and accommodation:
        st.info(
            f"🏨 **Проживание:** {accommodation.get('type', '')} "
            f"в районе {accommodation.get('area', '')} · "
            f"~{accommodation.get('price_per_night', 0)} {curr}/ночь. "
            f"{accommodation.get('why', '')}"
        )

    elif not hotels and isinstance(accommodation, list) and accommodation:
        st.subheader("🏨 Варианты проживания")

        for hotel in accommodation:
            with st.container(border=True):
                h1, h2 = st.columns([3, 1])

                hotel_name = hotel.get("name", "Вариант проживания")
                hotel_tier = hotel.get("tier", "")
                hotel_area = hotel.get("area", "")
                hotel_why = hotel.get("why", "")
                hotel_price = hotel.get("price_per_night", 0)

                h1.markdown(f"### {hotel_name}")
                h1.write(f"**Категория:** {hotel_tier}")
                h1.write(f"📍 Район: {hotel_area}")
                h1.write(hotel_why)

                h2.metric("За ночь", f"{hotel_price} {curr}")

    for day in data.get("days", []):
        day_number = day.get("day", "")
        day_date = day.get("date", "")
        day_theme = day.get("theme", "")
        day_vibe = day.get("vibe", "")

        header = (
            f"День {day_number} · {day_date} — {day_theme} "
            f"· {day_vibe}"
        )

        with st.expander(header, expanded=(day_number == 1)):
            for activity in day.get("activities", []):
                activity_type = activity.get("type", "")
                icon = ICONS.get(activity_type, "📍")

                time_value = activity.get("time", "")
                title = activity.get("title", "")
                duration = activity.get("duration_min", "?")
                cost = activity.get("cost", 0)
                location = activity.get("location", "")
                description = activity.get("description", "")
                tip = activity.get("tip", "")

                st.markdown(
                    f"**{time_value}** {icon} **{title}** · "
                    f"{duration} мин · ~{cost} {curr}  \n"
                    f"📍 {location}  \n"
                    f"{description}"
                )

                if tip:
                    st.caption(f"💡 {tip}")

            st.markdown(
                f"**Итого за день:** ~{day.get('day_cost', 0)} {curr}"
            )


# ---------- ВКЛАДКА 2. КАРТА ----------

with tabs[1]:
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
        st.info("Для этой поездки модель не вернула координаты для карты.")
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

            popup_html = (
                f"День {day_number} · {activity.get('time', '')}<br>"
                f"<b>{activity.get('title', '')}</b><br>"
                f"{activity.get('location', '')}"
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
                    opacity=0.7,
                    color="#22d3ee",
                ).add_to(fmap)

        st_folium(
            fmap,
            use_container_width=True,
            height=520,
            returned_objects=[],
        )

        st.caption("Картографические данные: © OpenStreetMap contributors")


# ---------- ВКЛАДКА 3. ПЛАН / ФАКТ ----------

with tabs[2]:
    st.caption(
        "Введите фактические траты и нажмите кнопку сохранения. "
        "Отклонение от плана пересчитается автоматически."
    )

    if not expenses:
        st.info("Для этой поездки пока нет расходов.")
    else:
        for expense in expenses:
            c1, c2, c3, c4 = st.columns([4, 1, 2, 1])

            day_number = expense["day"]
            category = expense["category"]
            title = expense["title"]
            plan_cost = expense["cost_plan"] or 0
            actual_cost = expense["cost_actual"] or 0

            c1.text(
                f"День {day_number} · "
                f"{ICONS.get(category, '•')} {title}"
            )

            c2.text(f"План: {plan_cost:.0f}")

            actual_value = c3.number_input(
                "Факт",
                min_value=0.0,
                value=float(actual_cost),
                step=10.0,
                key=f"actual_{expense['id']}",
                label_visibility="collapsed",
            )

            if c4.button("💾", key=f"save_{expense['id']}"):
                db.update_expense_actual(expense["id"], actual_value)
                st.toast("Расход сохранён")
                st.rerun()

    budget_breakdown = data.get("budget_breakdown") or {}

    if budget_breakdown:
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

        st.subheader("Структура планового бюджета")
        st.bar_chart(chart_data)
        st.dataframe(chart_data, use_container_width=True)

        total_by_categories = chart_data["План"].sum()

        st.caption(
            f"Сумма по категориям: {total_by_categories:.0f} {curr}"
        )


# ---------- ВКЛАДКА 4. ПОЛЕЗНОЕ ----------

with tabs[3]:
    wow_moments = data.get("wow_moments") or []

    if wow_moments:
        st.subheader("✨ Главные впечатления")

        for moment in wow_moments:
            st.markdown(f"- {moment}")

    packing = data.get("packing") or []

    if packing:
        st.subheader("🎒 Что взять с собой")

        for index, item in enumerate(packing):
            st.checkbox(
                item,
                key=f"packing_{trip_id}_{index}",
            )

    phrases = data.get("phrases") or []

    if phrases:
        st.subheader("💬 Полезные фразы")

        for phrase in phrases:
            russian = phrase.get("ru", "")
            local = phrase.get("local", "")

            st.markdown(f"**{russian}** — _{local}_")

    tips = data.get("tips") or {}

    if tips:
        st.subheader("💡 Советы")

        for key, value in tips.items():
            title = TIP_RU.get(key, key)
            st.markdown(f"- **{title}:** {value}")


# ---------- ВКЛАДКА 5. JSON И СКАЧИВАНИЕ ----------

with tabs[4]:
    st.caption(
        "Эта вкладка показывает структурированный результат работы нейросети."
    )

    st.json(data)

    download_1, download_2 = st.columns(2)

    markdown_content = ai.to_markdown(data, curr)

    json_content = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
    )

    download_1.download_button(
        label="⬇️ Скачать маршрут в Markdown",
        data=markdown_content,
        file_name=f"travelmind_trip_{trip_id}.md",
        mime="text/markdown",
    )

    download_2.download_button(
        label="⬇️ Скачать маршрут в JSON",
        data=json_content,
        file_name=f"travelmind_trip_{trip_id}.json",
        mime="application/json",
    )
