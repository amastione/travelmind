"""Промпт и обращение к LLM для генерации маршрутов."""
import json
import re
from typing import Optional

import streamlit as st
from openai import OpenAI

PROMPT_VERSION = "v2.0"
MAX_DAYS = 7

# ---------- СИСТЕМНЫЙ ПРОМПТ ----------
# Постоянная часть. Меняется редко → кэшируется провайдером → дешевле.
SYSTEM_PROMPT = """Ты — опытный планировщик путешествий. Твоя цель — маршрут, оставляющий максимум положительных эмоций.

Правила:
- Отвечай ТОЛЬКО валидным JSON по схеме ниже. Без markdown, без текста вокруг.
- Все значения — на русском языке. Ключи — строго как в схеме.
- Указывай только реально существующие города и районы. Если не уверен в конкретном заведении, пиши тип и район («кафе с местной кухней в районе Бейоглу»), не выдумывай названия.
- Для КАЖДОЙ активности указывай координаты lat и lon (4 знака после запятой).
- Логистика: соседние по времени активности географически рядом, учитывай время на дорогу.
- Стоимости — оценочные, в валюте пользователя, на всю группу. Сумма budget_breakdown не превышает бюджет. total_cost — реальная сумма плана, НЕ копия бюджета.
- Описания — до 20 слов, живым языком. tip — короткий практичный совет.
- Темп: slow — 2-3 активности в день, medium — 3-4, fast — 5-6 (приёмы пищи не считаются).
- type: A=достопримечательность, F=еда, T=транспорт, S=проживание, L=отдых, H=шопинг, W=wow-момент.
- wow_moments — 1-3 самых запоминающихся впечатления за поездку.
- mood_score — ожидаемая оценка настроения от 1 до 10, mood_reason — одно предложение почему.
- packing — 5-8 вещей именно под эту поездку (сезон, активности).
- phrases — 5 полезных фраз с переводом, если местный язык отличается от русского.

Схема:
{"title":str,"overview":str,"total_cost":num,"mood_score":int,"mood_reason":str,
"accommodation":{"area":str,"type":str,"price_per_night":num,"why":str},
"days":[{"day":int,"date":"YYYY-MM-DD","theme":str,"vibe":str,
"activities":[{"time":"HH:MM","duration_min":int,"title":str,"type":"A|F|T|S|L|H|W","location":str,"lat":num,"lon":num,"description":str,"cost":num,"tip":str}],
"day_cost":num}],
"budget_breakdown":{"accommodation":num,"food":num,"activities":num,"transport":num,"other":num},
"wow_moments":[str],
"packing":[str],
"phrases":[{"ru":str,"local":str}],
"tips":{"transport":str,"safety":str,"culture":str,"money":str}}"""

# ---------- ШАБЛОН ПОЛЬЗОВАТЕЛЬСКОГО ЗАПРОСА ----------
# Меняется каждый раз. Короткий — экономим токены.
USER_TEMPLATE = """Направление: {dest}
Даты: {start} — {end} ({days} дн.)
Бюджет на всех: {budget} {curr} (без перелёта до места)
Путешественников: {people}
Стиль: {style}
Темп: {pace}
Интересы: {interests}
Пожелания: {notes}"""


def build_prompt(dest, start, end, days, budget, curr, people,
                 style, pace, interests, notes) -> str:
    """Собирает пользовательский запрос из параметров формы."""
    return USER_TEMPLATE.format(
        dest=dest, start=start, end=end, days=days, budget=budget,
        curr=curr, people=people, style=style, pace=pace,
        interests=interests or "любые", notes=notes or "нет",
    )


def _parse_json(text: str) -> dict:
    """Достаёт JSON, даже если модель обернула его в ```json ... ```."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    return json.loads(text)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def generate(user_prompt: str) -> dict:
    """Запрос к модели. Одинаковые запросы кэшируются на 24 часа."""
    client = OpenAI(
        api_key=st.secrets["LLM_API_KEY"],
        base_url=st.secrets.get("LLM_BASE_URL", "https://api.deepseek.com"),
    )
    resp = client.chat.completions.create(
        model=st.secrets.get("LLM_MODEL", "deepseek-chat"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=6000,
        response_format={"type": "json_object"},
    )
    return {
        "data": _parse_json(resp.choices[0].message.content),
        "tokens_in": resp.usage.prompt_tokens,
        "tokens_out": resp.usage.completion_tokens,
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
    for d in days:
        if not d.get("activities"):
            errors.append(f"День {d.get('day')}: нет активностей.")
    if not data.get("accommodation"):
        errors.append("Нет рекомендаций по проживанию.")
    return errors


def to_markdown(data: dict, curr: str) -> str:
    """Экспорт маршрута в читаемый текст."""
    lines = [f"# {data.get('title', 'Маршрут')}", "", data.get("overview", ""), ""]
    acc = data.get("accommodation") or {}
    if acc:
        lines.append(f"**Проживание:** {acc.get('type', '')} · "
                     f"район {acc.get('area', '')} · "
                     f"~{acc.get('price_per_night', 0)} {curr}/ночь")
        lines.append("")
    for d in data.get("days", []):
        lines.append(f"## День {d.get('day')} · {d.get('date', '')} — "
                     f"{d.get('theme', '')}")
        for a in d.get("activities", []):
            lines.append(
                f"- **{a.get('time', '')}** {a.get('title', '')} — "
                f"{a.get('location', '')}, ~{a.get('cost', 0)} {curr}. "
                f"{a.get('description', '')}"
            )
        lines.append(f"\nИтого за день: ~{d.get('day_cost', 0)} {curr}\n")
    wm = data.get("wow_moments") or []
    if wm:
        lines.append("## Главные впечатления")
        lines += [f"- {w}" for w in wm]
        lines.append("")
    packing = data.get("packing") or []
    if packing:
        lines.append("## Что взять с собой")
        lines += [f"- [ ] {p}" for p in packing]
    return "\n".join(lines)
