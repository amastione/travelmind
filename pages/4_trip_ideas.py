"""Страница AI-подбора направлений для короткой поездки."""

import json
from html import escape

import streamlit as st

import ai
import auth
import branding
import site_access


st.set_page_config(
    page_title="Идеи для поездки",
    page_icon="✨",
    layout="wide",
)

branding.apply_clean_layout()
site_access.require_site_access()
user_id = auth.require_auth()
# ==========================================================
# ОЧИСТКА РЕЗУЛЬТАТА ПРОШЛОЙ ГЕНЕРАЦИИ
# ==========================================================
# Пользователь перешёл в модуль поиска идей, поэтому старый
# экран «Маршрут готов» на странице планирования больше не нужен.
st.session_state.pop("generated_trip_id", None)
st.session_state.pop("generated_tokens_in", None)
st.session_state.pop("generated_tokens_out", None)
st.session_state.pop("pending_trip_generation", None)


CSS = """
<style>
.stApp {
    background:
        radial-gradient(
            circle at 10% 8%,
            rgba(34, 211, 238, 0.12),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 88%,
            rgba(139, 92, 246, 0.15),
            transparent 36%
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
    max-width: 1180px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

#MainMenu,
footer {
    visibility: hidden;
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
    margin: 0.7rem 0 1.5rem;
    color: #AAB8CE;
    font-size: 1.05rem;
    line-height: 1.6;
}

.tm-info-card {
    margin: 1rem 0 1.4rem;
    padding: 1rem 1.15rem;
    border: 1px solid rgba(34, 211, 238, 0.20);
    border-radius: 16px;
    background: rgba(34, 211, 238, 0.06);
    color: #C9D7E8;
    line-height: 1.55;
}

[data-testid="stForm"] {
    padding: 1.6rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 22px;
    background: rgba(15, 23, 42, 0.72);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
}

.tm-result-summary {
    margin: 1.6rem 0 1rem;
    padding: 1rem 1.15rem;
    border: 1px solid rgba(125, 211, 252, 0.24);
    border-radius: 16px;
    background: rgba(30, 41, 59, 0.62);
    color: #DCE8F8;
    line-height: 1.55;
}

.tm-idea-card {
    display: flex;
    flex-direction: column;

    height: 390px;
    box-sizing: border-box;

    margin-bottom: 0.7rem;
    padding: 1.25rem;

    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 20px;

    background:
        linear-gradient(
            135deg,
            rgba(30, 41, 59, 0.72),
            rgba(15, 23, 42, 0.80)
        );

    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.06),
        0 12px 30px rgba(0, 0, 0, 0.15);
}

.tm-idea-title {
    color: #F8FAFC;
    font-size: 1.22rem;
    font-weight: 800;
    line-height: 1.28;
}

.tm-idea-place {
    margin-top: 0.38rem;
    color: #9FB2CB;
    font-size: 0.92rem;
}

.tm-idea-meta {
    margin-top: 0.85rem;
    color: #C7D7E9;
    font-size: 0.9rem;
    line-height: 1.7;
}

.tm-idea-why {
    margin-top: 0.85rem;
    color: #E4EDF8;
    font-size: 0.94rem;
    line-height: 1.55;
}

.tm-idea-highlights {
    max-height: 78px;
    margin: 0.8rem 0 0;
    padding-left: 1.1rem;
    overflow: hidden;
    color: #AABDD4;
    font-size: 0.9rem;
    line-height: 1.55;
}

.tm-caution {
    margin-top: 0.85rem;
    color: #FCD34D;
    font-size: 0.88rem;
    line-height: 1.5;
}

.tm-idea-transport {
    margin-top: auto;
    padding-top: 0.8rem;
    border-top: 1px solid rgba(148, 163, 184, 0.16);
    color: #AABDD4;
    font-size: 0.86rem;
    line-height: 1.45;
}


@media (max-width: 640px) {
    .block-container {
        padding: 1.8rem 1rem 3rem;
    }

    .tm-page-title {
        font-size: 2rem !important;
    }

    [data-testid="stForm"] {
        padding: 1.1rem;
    }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)
branding.apply_glass_buttons()
branding.show_author_mark()

# Локальные исправления формы и кнопки навигации.
# Добавляются после общего glass-стиля, поэтому имеют приоритет.
st.markdown(
    """
    <style>
    /* ------------------------------------------------------
       ГЛАВНОЕ МЕНЮ: одинаковый размер и центрирование текста
       ------------------------------------------------------ */

    section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"],
    [data-testid="stPageLink-NavLink"] {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;

        width: 100% !important;
        min-height: 48px !important;
        box-sizing: border-box !important;

        text-align: center !important;
    }

    section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"] p,
    [data-testid="stPageLink-NavLink"] p {
        width: auto !important;
        margin: 0 !important;
        color: #F8FAFC !important;
        text-align: center !important;
    }

    /* ------------------------------------------------------
       ПОДПИСИ И ТЕКСТ В ФОРМЕ
       ------------------------------------------------------ */

    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] label,
    [data-testid="stWidgetLabel"] label p,
    [data-testid="stWidgetLabel"] div {
        color: #F8FAFC !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }

    /* Подписи вариантов radio: «Рядом...» / «По пути...» */
    .stRadio label,
    .stRadio label p,
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] label p {
        color: #E8F0FA !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    /* ------------------------------------------------------
       ПОЛЯ ВВОДА: тёмное стекло + читаемый светлый текст
   ------------------------------------------------------ */

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input {
        border: 1px solid rgba(148, 163, 184, 0.34) !important;
        border-radius: 13px !important;
    
        background: rgba(7, 11, 20, 0.78) !important;
        color: #F8FAFC !important;
    
        box-shadow:
            inset 0 1px 0 rgba(255, 255, 255, 0.04),
            inset 0 -1px 0 rgba(0, 0, 0, 0.16) !important;
    }
    
    /* Убирает светлый фон, который Streamlit может добавить textarea */
    .stTextArea textarea {
        min-height: 110px !important;
    }
    
    /* Состояние фокуса */
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stNumberInput input:focus {
        border-color: rgba(103, 232, 249, 0.82) !important;
        background: rgba(7, 11, 20, 0.92) !important;
        box-shadow:
            0 0 0 3px rgba(34, 211, 238, 0.13),
            inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    }
    
    /* Текст-подсказка до ввода */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #94A3B8 !important;
        opacity: 1 !important;
    }

    /* Подсказки в пустых полях */
    .stTextInput input::placeholder,
    .stTextArea textarea::placeholder {
        color: #9AABC2 !important;
        opacity: 1 !important;
    }

    /* Радиокнопка при выборе */
    .stRadio [data-checked="true"] {
        color: #67E8F9 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

auth.render_main_menu_button()


THEME_ICONS = {
    "mountains": "🏔️",
    "nature": "🌲",
    "culture": "🏛️",
    "food": "🍜",
    "beach": "🏖️",
    "adventure": "🧭",
    "city": "🏙️",
    "mixed": "✈️",
}

INTERESTS = [
    "Горы и красивые дороги",
    "Природа, озёра и водопады",
    "История и культура",
    "Гастрономия и местная кухня",
    "Спа и термальные источники",
    "Прогулки и уютные города",
    "Активный отдых",
    "Фотография и видовые площадки",
    "Семейный отдых",
    "Нетуристические места",
]

TRANSPORTS = [
    "Автомобиль",
    "Общественный транспорт",
    "Смешанный транспорт",
]

BUDGETS = [
    "Экономный",
    "Средний",
    "Комфортный",
]


def build_idea_notes(idea: dict) -> str:
    """Собирает заметку, которая попадёт в форму создания маршрута."""
    highlights = idea.get("highlights") or []

    highlights_text = ", ".join(
        str(item).strip()
        for item in highlights[:3]
        if str(item).strip()
    )

    parts = [
        "Маршрут создан из модуля «Идеи для поездки».",
    ]

    why_it_fits = str(idea.get("why_it_fits") or "").strip()

    if why_it_fits:
        parts.append(f"Почему выбран вариант: {why_it_fits}")

    if highlights_text:
        parts.append(f"Хочу включить: {highlights_text}.")

    caution = str(idea.get("caution") or "").strip()

    if caution:
        parts.append(f"Важно учесть: {caution}")

    return " ".join(parts)


def render_idea_card(idea: dict, index: int) -> None:
    """Выводит карточку одной идеи одинаковой высоты."""
    theme = str(idea.get("theme") or "mixed").lower()
    icon = THEME_ICONS.get(theme, "✈️")

    title = escape(str(idea.get("title") or "Идея для поездки"))
    destination = escape(str(idea.get("destination") or ""))

    recommended_days = escape(
        str(idea.get("recommended_days") or "Уточняется")
    )

    budget_level = escape(
        str(idea.get("budget_level") or "средний")
    )

    transport_note = escape(
        str(idea.get("transport_note") or "")
    )

    why_it_fits = escape(
        str(idea.get("why_it_fits") or "")
    )

    caution = escape(
        str(idea.get("caution") or "")
    )

    try:
        distance = int(
            idea.get("estimated_distance_km") or 0
        )
    except (TypeError, ValueError):
        distance = 0

    distance_text = (
        f"≈ {distance} км"
        if distance > 0
        else "Расстояние уточняется"
    )

    highlights_items = []

    for item in idea.get("highlights") or []:
        item_text = escape(str(item).strip())

        if item_text:
            highlights_items.append(f"<li>{item_text}</li>")

    highlights_html = "".join(highlights_items)

    if not highlights_html:
        highlights_html = (
            "<li>Интересное направление для короткой поездки.</li>"
        )

    why_text = (
        why_it_fits
        or "Подходит под указанные параметры путешествия."
    )

    caution_html = ""

    if caution:
        caution_html = (
            f'<div class="tm-caution">⚠️ {caution}</div>'
        )

    transport_html = ""

    if transport_note:
        transport_html = (
            f'<div class="tm-idea-transport">'
            f'🚘 {transport_note}'
            f'</div>'
        )

    card_html = (
        f'<div class="tm-idea-card">'
        f'<div class="tm-idea-title">{icon} {title}</div>'
        f'<div class="tm-idea-place">📍 {destination}</div>'
        f'<div class="tm-idea-meta">'
        f'🚗 {distance_text}<br>'
        f'🕒 Оптимально: {recommended_days}<br>'
        f'💳 Бюджет: {budget_level}'
        f'</div>'
        f'<div class="tm-idea-why">'
        f'<b>Почему подходит:</b> {why_text}'
        f'</div>'
        f'<ul class="tm-idea-highlights">'
        f'{highlights_html}'
        f'</ul>'
        f'{caution_html}'
        f'{transport_html}'
        f'</div>'
    )

    st.markdown(
        card_html,
        unsafe_allow_html=True,
    )

    if st.button(
        "✨ Выбрать и создать маршрут",
        key=f"select_trip_idea_{index}",
        use_container_width=True,
    ):
        st.session_state["trip_idea_prefill"] = {
            "destination": str(
                idea.get("destination") or ""
            ).strip(),
            "notes": build_idea_notes(idea),
            "title": str(idea.get("title") or "").strip(),
            "theme": theme,
            "cover_profile": str(
                idea.get("cover_profile") or ""
            ).strip(),
        }

        st.switch_page("pages/1_new_trip.py")


st.markdown(
    '<div class="tm-page-eyebrow">TravelMind AI · Travel inspiration</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<h1 class="tm-page-title">✨ Идеи для поездки</h1>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="tm-page-description">
        Укажите район, свободное время и интересы — TravelMind предложит
        несколько направлений. Можно искать места рядом или выбрать
        интересную остановку по пути.
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="tm-info-card">
        Пример: <b>Грозный → Минеральные Воды</b>, два свободных дня,
        автомобиль и интерес к горам. AI предложит варианты вроде Чегемского
        ущелья, Приэльбрусья, Верхней Балкарии или других подходящих мест.
        Расстояния являются ориентировочными.
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("trip_ideas_form"):
    search_mode_label = st.radio(
        "Как искать идеи?",
        [
            "Рядом с выбранной местностью",
            "По пути к месту назначения",
        ],
        horizontal=True,
    )

    origin = st.text_input(
        "Откуда или в какой местности хотите искать?",
        placeholder=(
            "Например: Грозный, Кавказские Минеральные Воды, "
            "Кавказ, Республика Дагестан"
        ),
        help=(
            "Необязательно указывать точную точку. "
            "Можно написать регион или примерную местность."
        ),
    )

    destination = ""

    if search_mode_label == "По пути к месту назначения":
        destination = st.text_input(
            "Куда направляетесь?",
            placeholder="Например: Минеральные Воды",
        )

    column_1, column_2, column_3 = st.columns(3)

    with column_1:
        radius_km = st.slider(
            (
                "Допустимый крюк, км"
                if search_mode_label == "По пути к месту назначения"
                else "Радиус поиска, км"
            ),
            min_value=50,
            max_value=700,
            value=250,
            step=50,
        )

    with column_2:
        days = st.selectbox(
            "Сколько свободных дней?",
            [1, 2, 3, 4, 5, 6, 7],
            index=1,
        )

    with column_3:
        transport = st.selectbox(
            "Транспорт",
            TRANSPORTS,
        )

    column_4, column_5 = st.columns(2)

    with column_4:
        budget = st.selectbox(
            "Формат бюджета",
            BUDGETS,
            index=1,
        )

    with column_5:
        interests = st.multiselect(
            "Что интересно?",
            INTERESTS,
            default=[
                "Природа, озёра и водопады",
                "Горы и красивые дороги",
            ],
        )

    notes = st.text_area(
        "Дополнительные пожелания",
        placeholder=(
            "Например: нужна спокойная поездка с ночёвкой, "
            "без сложных пеших маршрутов, хочется красивую дорогу."
        ),
    )

    submitted = st.form_submit_button(
        "✨ Найти идеи с AI",
        use_container_width=True,
    )

if submitted:
    search_mode = (
        "on_the_way"
        if search_mode_label == "По пути к месту назначения"
        else "nearby"
    )

    request_data = {
        "search_mode": search_mode,
        "origin": origin.strip(),
        "destination": destination.strip(),
        "radius_km": radius_km,
        "days": days,
        "transport": transport,
        "budget": budget,
        "interests": interests,
        "notes": notes.strip(),
    }

    if not request_data["origin"]:
        st.error("Укажите стартовую точку или примерную местность.")
        st.stop()

    if search_mode == "on_the_way" and not request_data["destination"]:
        st.error("Для поиска по пути укажите конечную точку.")
        st.stop()

    request_json = json.dumps(
        request_data,
        ensure_ascii=False,
        sort_keys=True,
    )

    with st.spinner(
        "✦ TravelMind ищет подходящие направления… "
        "обычно это занимает 15–40 секунд."
    ):
        try:
            result = ai.generate_trip_ideas(request_json)

        except Exception as error:
            st.error(
                "Не удалось подобрать идеи. Уточните местность, "
                "увеличьте радиус или попробуйте ещё раз."
            )
            st.caption(f"Техническая причина: {str(error)[:250]}")
            st.stop()

    st.session_state["trip_ideas_result"] = result["data"]
    st.session_state["trip_ideas_tokens_in"] = result.get("tokens_in", 0)
    st.session_state["trip_ideas_tokens_out"] = result.get("tokens_out", 0)

trip_ideas_result = st.session_state.get("trip_ideas_result")

if trip_ideas_result:
    summary = str(
        trip_ideas_result.get("search_summary") or ""
    ).strip()

    if summary:
        st.markdown(
            f"""
            <div class="tm-result-summary">
                <b>AI-рекомендация:</b> {escape(summary)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    tokens_in = st.session_state.get("trip_ideas_tokens_in")
    tokens_out = st.session_state.get("trip_ideas_tokens_out")

    if tokens_in is not None and tokens_out is not None:
        st.caption(
            f"Использовано токенов: {tokens_in} вход / {tokens_out} выход."
        )

    st.subheader("Подходящие направления")

    ideas = trip_ideas_result.get("ideas") or []

    for index in range(0, len(ideas), 2):
        left_column, right_column = st.columns(2)

        with left_column:
            render_idea_card(ideas[index], index)

        if index + 1 < len(ideas):
            with right_column:
                render_idea_card(ideas[index + 1], index + 1)
