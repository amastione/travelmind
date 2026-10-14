"""Промпт и обращение к LLM для генерации маршрутов."""
import json
import re

import streamlit as st
from openai import OpenAI

PROMPT_VERSION = "v3.0"
MAX_DAYS = 7

# ---------- СИСТЕМНЫЙ ПРОМПТ ----------
# Постоянная часть запроса. Провайдер может кэшировать её,
# что уменьшает стоимость повторных обращений к модели.
SYSTEM_PROMPT = """Ты — опытный AI-планировщик путешествий.
Твоя цель — создать реалистичный, персонализированный и удобный маршрут.

ОБЩИЕ ПРАВИЛА:
- Отвечай ТОЛЬКО валидным JSON строго по схеме ниже.
- Не используй markdown, комментарии или текст вне JSON.
- Все значения — на русском языке. Ключи — строго как в схеме.
- Указывай только реально существующие города, районы и достопримечательности.
- Если не уверен в названии кафе, ресторана или малого заведения, не выдумывай его:
  пиши тип и район, например: «кафе с местной кухней в районе Бейоглу».
- Для каждой активности обязательно указывай координаты lat и lon
  с точностью до 4 знаков после запятой.
- Соседние по времени активности должны быть географически близки.
  Учитывай дорогу, режим работы и реалистичное время посещения.
- Стоимости оценочные, в валюте пользователя и на всю группу,
  если не указано обратное.
- Сумма budget_breakdown не превышает бюджет пользователя.
- total_cost — расчётная стоимость маршрута, а не простое повторение бюджета.
- Описание активности: максимум 20 слов. tip — краткий практичный совет.
- Темп slow: 2–3 активности в день; medium: 3–4; fast: 5–6.
  Приёмы пищи не учитываются как активности темпа.
- type: A=достопримечательность, F=еда, T=транспорт,
  S=проживание, L=отдых, H=шопинг, W=wow-момент.
- wow_moments: от 1 до 3 самых ярких впечатлений.
- mood_score: ожидаемая оценка настроения от 1 до 10.
- packing: 5–8 вещей с учётом сезона и запланированных активностей.
- phrases: 5 полезных фраз, если местный язык отличается от русского.

ОБЛОЖКА ПОЕЗДКИ:
- cover_theme выбери строго из: city, mountains, beach, culture, food,
  nature, adventure, mixed.
- city: городская панорама; mountains: горы/озёра/трекинг;
  beach: море/пляж; culture: архитектура/история; food: гастрономия;
  nature: парки/леса/водопады; adventure: активный отдых; mixed: путешествие смешанного типа.

ОТЕЛИ:
- Верни ровно 3 объекта в hotels в порядке:
  1) «Эконом», 2) «Оптимальный», 3) «Премиум».
- Рекомендуй реально существующие и известные отели, только если уверен,
  что они существуют в указанном городе.
- Если не уверен в конкретном отеле, укажи честное обобщённое название:
  «Бюджетный отель в районе ...», «Бутик-отель в центре ...»,
  «Премиальный отель в районе ...». Не выдумывай бренды и рейтинги.
- rating: число от 0 до 10; ставь 0, если рейтинг неизвестен.
- Цены rooms — ориентировочные цены ЗА ОДИН НОМЕР ЗА ОДНУ НОЧЬ,
  не за всю группу и не за весь период.
- rooms.economy, rooms.standard, rooms.luxury — положительные числа.
  Для каждого следующего уровня цена должна быть выше предыдущего.
- Наличие номеров и цены не гарантируются: это учебный планировщик.
- В photo_queries укажи короткие английские запросы для изображений:
  exterior — фасад отеля, lobby — холл, room — интерьер номера.
  Не включай название отеля, логотипы, бренды и текст на фото.

СХЕМА JSON:
{
  "title": str,
  "overview": str,
  "cover_theme": "city|mountains|beach|culture|food|nature|adventure|mixed",
  "total_cost": num,
  "mood_score": int,
  "mood_reason": str,

  "accommodation": {
    "area": str,
    "type": str,
    "price_per_night": num,
    "why": str
  },

  "hotels": [
    {
      "tier": "Эконом|Оптимальный|Премиум",
      "name": str,
      "area": str,
      "rating": num,
      "why": str,
      "map_query": str,
      "rooms": {
        "economy": num,
        "standard": num,
        "luxury": num
      },
      "photo_queries": {
        "exterior": str,
        "lobby": str,
        "room": str
      }
    }
  ],

  "days": [
    {
      "day": int,
      "date": "YYYY-MM-DD",
      "theme": str,
      "vibe": str,
      "activities": [
        {
          "time": "HH:MM",
          "duration_min": int,
          "title": str,
          "type": "A|F|T|S|L|H|W",
          "location": str,
          "lat": num,
          "lon": num,
          "description": str,
          "cost": num,
          "tip": str
        }
      ],
      "day_cost": num
    }
  ],

  "budget_breakdown": {
    "accommodation": num,
    "food": num,
    "activities": num,
    "transport": num,
    "other": num
  },

  "wow_moments": [str],
  "packing": [str],
  "phrases": [{"ru": str, "local": str}],
  "tips": {
    "transport": str,
    "safety": str,
    "culture": str,
    "money": str
  }
}"""


# ---------- ШАБЛОН ПОЛЬЗОВАТЕЛЬСКОГО ЗАПРОСА ----------
# Переменная часть намеренно короткая: это снижает число входных токенов.
USER_TEMPLATE = """Версия пресета: v3.0
Направление: {dest}
Даты: {start} — {end} ({days} дн.)
Бюджет на всех без перелёта: {budget} {curr}
Путешественников: {people}
Стиль: {style}
Темп: {pace}
Интересы: {interests}
Пожелания: {notes}"""


def build_prompt(
    dest,
    start,
    end,
    days,
    budget,
    curr,
    people,
    style,
    pace,
    interests,
    notes,
) -> str:
    """Собирает пользовательский запрос из параметров формы."""
    return USER_TEMPLATE.format(
        dest=dest,
        start=start,
        end=end,
        days=days,
        budget=budget,
        curr=curr,
        people=people,
        style=style,
        pace=pace,
        interests=interests or "любые",
        notes=notes or "нет",
    )


def _parse_json(text: str) -> dict:
    """Извлекает JSON, даже если модель обернула его в блок ```json."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def generate(user_prompt: str) -> dict:
    """Запрос к модели. Одинаковые запросы кэшируются на 24 часа."""
    client = OpenAI(
        api_key=st.secrets["LLM_API_KEY"],
        base_url=st.secrets.get(
            "LLM_BASE_URL",
            "https://api.deepseek.com",
        ),
    )

    response = client.chat.completions.create(
        model=st.secrets.get("LLM_MODEL", "deepseek-chat"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=6500,
        response_format={"type": "json_object"},
    )

    return {
        "data": _parse_json(response.choices[0].message.content),
        "tokens_in": response.usage.prompt_tokens,
        "tokens_out": response.usage.completion_tokens,
    }


def validate(data: dict) -> list:
    """Базовая проверка структуры ответа. Возвращает список замечаний."""
    errors = []

    if not data.get("title"):
        errors.append("Модель не вернула название маршрута.")

    days = data.get("days")
    if not isinstance(days, list) or not days:
        errors.append("В ответе нет списка дней.")
        return errors

    for day in days:
        if not day.get("activities"):
            errors.append(f"День {day.get('day')}: нет активностей.")

    if not data.get("accommodation"):
        errors.append("Нет основной рекомендации по проживанию.")

    hotels = data.get("hotels")
    if not isinstance(hotels, list) or len(hotels) != 3:
        errors.append("Модель не вернула 3 варианта отелей.")
    else:
        expected_tiers = ["Эконом", "Оптимальный", "Премиум"]

        for index, hotel in enumerate(hotels):
            if hotel.get("tier") != expected_tiers[index]:
                errors.append(
                    "Нарушен порядок вариантов отелей: "
                    "Эконом → Оптимальный → Премиум."
                )
                break

            rooms = hotel.get("rooms")
            if not isinstance(rooms, dict):
                errors.append(
                    f"У отеля «{hotel.get('name', 'без названия')}» "
                    "нет цен по категориям номеров."
                )

    return errors


def to_markdown(data: dict, curr: str) -> str:
    """Экспорт маршрута в читаемый Markdown-текст."""
    lines = [
        f"# {data.get('title', 'Маршрут')}",
        "",
        data.get("overview", ""),
        "",
    ]

    hotels = data.get("hotels") or []

    if hotels:
        lines.extend(
            [
                "## Где остановиться",
                "",
                (
                    "> Цены ориентировочные и указаны за один номер "
                    "на одну ночь. Уточняйте стоимость и наличие "
                    "на официальном сайте отеля или в сервисе бронирования."
                ),
                "",
            ]
        )

        for hotel in hotels:
            rooms = hotel.get("rooms") or {}

            lines.extend(
                [
                    f"### {hotel.get('tier', 'Вариант')} — "
                    f"{hotel.get('name', 'Отель')}",
                    f"- Район: {hotel.get('area', '—')}",
                    f"- Рейтинг: {hotel.get('rating', '—')}/10",
                    f"- Почему подходит: {hotel.get('why', '')}",
                    (
                        f"- Эконом: от {rooms.get('economy', 0)} "
                        f"{curr}/ночь"
                    ),
                    (
                        f"- Стандарт: от {rooms.get('standard', 0)} "
                        f"{curr}/ночь"
                    ),
                    (
                        f"- Люкс: от {rooms.get('luxury', 0)} "
                        f"{curr}/ночь"
                    ),
                    "",
                ]
            )

    else:
        # Поддержка старых маршрутов, созданных до версии v3.0
        accommodation = data.get("accommodation") or {}

        if accommodation:
            lines.extend(
                [
                    (
                        f"**Проживание:** {accommodation.get('type', '')} · "
                        f"район {accommodation.get('area', '')} · "
                        f"~{accommodation.get('price_per_night', 0)} "
                        f"{curr}/ночь"
                    ),
                    "",
                ]
            )

    for day in data.get("days", []):
        lines.append(
            f"## День {day.get('day')} · {day.get('date', '')} — "
            f"{day.get('theme', '')}"
        )

        for activity in day.get("activities", []):
            lines.append(
                f"- **{activity.get('time', '')}** "
                f"{activity.get('title', '')} — "
                f"{activity.get('location', '')}, "
                f"~{activity.get('cost', 0)} {curr}. "
                f"{activity.get('description', '')}"
            )

        lines.append(
            f"\nИтого за день: ~{day.get('day_cost', 0)} {curr}\n"
        )

    wow_moments = data.get("wow_moments") or []

    if wow_moments:
        lines.append("## Главные впечатления")
        lines.extend(f"- {moment}" for moment in wow_moments)
        lines.append("")

    packing = data.get("packing") or []

    if packing:
        lines.append("## Что взять с собой")
        lines.extend(f"- [ ] {item}" for item in packing)

    return "\n".join(lines)
