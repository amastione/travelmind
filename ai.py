"""Промпт и обращение к LLM для генерации маршрутов."""

import json
import re

import streamlit as st
from openai import OpenAI


PROMPT_VERSION = "v3.1"
MAX_DAYS = 7


# ==========================================================
# ДОПУСТИМЫЕ ПРОФИЛИ ОБЛОЖЕК
# ==========================================================

ALLOWED_COVER_PROFILES = {
    "city_summer",
    "city_autumn",
    "city_winter",
    "moscow",
    "saint_peter",
    "sochi",
    "northern_city_autumn",
    "northern_city_winter",
    "caucasus_summer",
    "caucasus_winter",
    "mountains_summer",
    "mountains_winter",
    "sea_summer",
    "sea_sunset",
    "europe_city",
    "europe_winter",
    "tropical_island",
    "desert_city",
}


# ==========================================================
# СИСТЕМНЫЙ ПРОМПТ ДЛЯ ГЕНЕРАЦИИ МАРШРУТА
# ==========================================================

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
  nature: парки/леса/водопады; adventure: активный отдых;
  mixed: путешествие смешанного типа.

Также обязательно верни поле cover_profile.
cover_profile — это профиль изображения для визуальной обложки маршрута.
Выбери РОВНО ОДНО значение строго из списка:
city_summer, city_autumn, city_winter,
moscow, saint_peter, sochi,
northern_city_autumn, northern_city_winter,
caucasus_summer, caucasus_winter,
mountains_summer, mountains_winter,
sea_summer, sea_sunset,
europe_city, europe_winter,
tropical_island, desert_city.

ПРАВИЛА ВЫБОРА cover_profile:
- Москва и ближайшая московская агломерация → moscow.
- Санкт-Петербург, Петергоф, Пушкин, Павловск, Кронштадт → saint_peter.
- Сочи, Адлер, Красная Поляна, Роза Хутор → sochi.
- Домбай, Архыз, Эльбрус, Приэльбрусье, Северный Кавказ:
  зимой → caucasus_winter; в остальные сезоны → caucasus_summer.
- Другие горные направления:
  зимой → mountains_winter; в остальные сезоны → mountains_summer.
- Северные города:
  зимой → northern_city_winter; в другие сезоны → northern_city_autumn.
- Морские и пляжные курорты:
  весной и летом → sea_summer; осенью и зимой → sea_sunset.
- Европейские исторические города:
  зимой → europe_winter; в остальные сезоны → europe_city.
- Тропические острова → tropical_island.
- Дубай, ОАЭ, пустынные и восточные города → desert_city.
- Если направление нельзя уверенно отнести к категории:
  зимой → city_winter;
  осенью → city_autumn;
  весной или летом → city_summer.
- Не придумывай новые значения cover_profile.

ОТЕЛИ:
- Верни ровно 3 объекта в hotels в порядке:
  1) «Эконом», 2) «Оптимальный», 3) «Премиум».
- Рекомендуй реально существующие и известные отели, только если уверен,
  что они существуют в указанном городе.
- Если не уверен в конкретном отеле, укажи честное обобщённое название:
  «Бюджетный отель в районе ...», «Бутик-отель в центре ...»,
  «Премиальный отель в районе ...».
- rating: число от 0 до 10; ставь 0, если рейтинг неизвестен.
- Цены rooms — ориентировочные цены ЗА ОДИН НОМЕР ЗА ОДНУ НОЧЬ.
- rooms.economy, rooms.standard, rooms.luxury — положительные числа.
- Для каждого следующего уровня цена должна быть выше предыдущего.
- В photo_queries укажи короткие английские запросы для изображений.

СХЕМА JSON:
{
  "title": str,
  "overview": str,
  "cover_theme": "city|mountains|beach|culture|food|nature|adventure|mixed",
  "cover_profile": str,
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


# ==========================================================
# ШАБЛОН ПОЛЬЗОВАТЕЛЬСКОГО ЗАПРОСА
# ==========================================================

USER_TEMPLATE = """Версия пресета: v3.1
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
    """
    Надёжно извлекает первый полноценный JSON-объект из ответа модели.

    Поддерживает:
    - чистый JSON;
    - JSON в блоке ```json;
    - текст до/после JSON;
    - несколько фрагментов текста вокруг объекта.

    Если модель оборвала ответ до закрывающей скобки, функция честно
    возвращает ошибку: такой JSON нельзя безопасно восстановить.
    """
    if not text:
        raise json.JSONDecodeError(
            "Модель вернула пустой ответ.",
            "",
            0,
        )

    clean_text = str(text).strip().lstrip("\ufeff")

    clean_text = re.sub(
        r"^```(?:json)?\s*",
        "",
        clean_text,
        flags=re.IGNORECASE,
    )
    clean_text = re.sub(
        r"\s*```$",
        "",
        clean_text,
    ).strip()

    decoder = json.JSONDecoder()
    json_start = clean_text.find("{")
    last_error = None

    while json_start != -1:
        try:
            result, _ = decoder.raw_decode(
                clean_text[json_start:]
            )

            if isinstance(result, dict):
                return result

        except json.JSONDecodeError as error:
            last_error = error

        json_start = clean_text.find("{", json_start + 1)

    error_message = (
        "В ответе AI не найден полный валидный JSON-объект."
    )

    if last_error:
        error_message += (
            f" Причина: {last_error.msg} "
            f"(позиция {last_error.pos})."
        )

    raise json.JSONDecodeError(
        error_message,
        clean_text,
        0,
    )


def _create_llm_client() -> OpenAI:
    """Создаёт клиент совместимого с OpenAI API-провайдера."""
    return OpenAI(
        api_key=st.secrets["LLM_API_KEY"],
        base_url=st.secrets.get(
            "LLM_BASE_URL",
            "https://api.deepseek.com",
        ),
    )


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def generate(user_prompt: str) -> dict:
    """Генерирует маршрут. Идентичные запросы кэшируются 24 часа."""
    client = _create_llm_client()

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

    usage = response.usage

    return {
        "data": _parse_json(response.choices[0].message.content),
        "tokens_in": getattr(usage, "prompt_tokens", 0) or 0,
        "tokens_out": getattr(usage, "completion_tokens", 0) or 0,
    }


# ==========================================================
# AI-РЕДАКТИРОВАНИЕ СОХРАНЁННОГО МАРШРУТА
# ==========================================================

EDIT_SYSTEM_PROMPT = """Ты — AI-редактор маршрутов TravelMind.

Твоя задача: изменить существующий туристический маршрут по просьбе
пользователя, сохранив валидную JSON-структуру TravelMind.

СТРОГИЕ ПРАВИЛА:
- Верни ТОЛЬКО валидный JSON.
- Не используй Markdown, комментарии, пояснения или текст вне JSON.
- Все значения должны быть на русском языке.
- Сохрани ВСЕ ключи и общую JSON-схему исходного маршрута.
- Не удаляй поля: title, overview, cover_theme, cover_profile,
  total_cost, mood_score, mood_reason, accommodation, hotels, days,
  budget_breakdown, wow_moments, packing, phrases, tips.
- Сохрани направление, даты поездки, количество дней, валюту
  и количество путешественников.
- Номера дней и даты в days не меняй.
- Можно менять активности, отели, стоимость, советы, описание,
  список вещей и другие рекомендации, если этого требует пользователь.
- Используй только реально существующие города, районы
  и достопримечательности.
- Для каждой активности обязательно сохрани lat и lon.
- Соседние активности одного дня должны быть логично расположены
  и реалистично укладываться по времени.
- Каждый день должен содержать хотя бы одну активность.
- Пересчитай activity.cost, day_cost, total_cost и budget_breakdown.
- budget_breakdown не должен превышать общий бюджет пользователя,
  если пользователь не попросил увеличить бюджет.
"""


def edit_trip_with_ai(
    current_data: dict,
    trip_context: dict,
    user_request: str,
) -> dict:
    """
    Изменяет сохранённый маршрут по команде пользователя.

    Модель обязана вернуть полный маршрут TravelMind, а не только
    список изменений. При неполной структуре выполняется одна
    дополнительная попытка с уточнением.
    """
    destination = str(trip_context.get("destination") or "")
    start_date = str(trip_context.get("start_date") or "")
    end_date = str(trip_context.get("end_date") or "")
    budget = trip_context.get("budget") or 0
    currency = str(trip_context.get("currency") or "RUB")
    people = trip_context.get("people") or 1

    # Служебную историю AI-команд не отправляем в LLM:
    # она не относится к структуре маршрута и увеличивает контекст.
    editable_data = dict(current_data)
    editable_data.pop("_ai_edit_history", None)

    current_json = json.dumps(
        editable_data,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    base_prompt = f"""КОНТЕКСТ ПОЕЗДКИ:
Направление: {destination}
Даты: {start_date} — {end_date}
Исходный бюджет: {budget} {currency}
Путешественников: {people}

КОМАНДА ПОЛЬЗОВАТЕЛЯ:
{user_request}

ТЕКУЩИЙ МАРШРУТ В JSON:
{current_json}

ЗАДАЧА:
Внеси только необходимые изменения в маршрут согласно команде пользователя.

КРИТИЧЕСКОЕ ТРЕБОВАНИЕ:
Верни не список изменений и не частичный JSON, а ПОЛНУЮ новую версию
маршрута строго по JSON-схеме из системной инструкции.

Обязательно сохрани и верни все верхнеуровневые поля:
title, overview, cover_theme, cover_profile, total_cost, mood_score,
mood_reason, accommodation, hotels, days, budget_breakdown,
wow_moments, packing, phrases, tips.

Верни только один завершённый JSON-объект без Markdown и пояснений."""

    client = _create_llm_client()
    last_error = None

    # Две попытки: обычная и исправляющая, если модель вернула
    # сокращённую/неполную структуру.
    for attempt in range(2):
        retry_note = ""

        if attempt == 1:
            retry_note = """

ПРЕДЫДУЩИЙ ОТВЕТ БЫЛ ОТКЛОНЁН, ПОТОМУ ЧТО ОН БЫЛ НЕПОЛНЫМ.
Не возвращай только изменённые поля.

Особенно проверь наличие title, cover_profile и полного списка days.
Верни весь маршрут целиком по полной схеме JSON."""

        try:
            response = client.chat.completions.create(
                model=st.secrets.get("LLM_MODEL", "deepseek-chat"),
                messages=[
                    # SYSTEM_PROMPT содержит полную схему TravelMind.
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    {
                        "role": "system",
                        "content": EDIT_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": base_prompt + retry_note,
                    },
                ],
                temperature=0.2,
                max_tokens=8192,
                response_format={"type": "json_object"},
            )

            content = str(
                response.choices[0].message.content or ""
            ).strip()

            if not content:
                raise ValueError("AI вернул пустой ответ.")

            parsed_data = _parse_json(content)

            # Проверяем структуру до возврата результата в страницу.
            # Благодаря этому можно автоматически повторить запрос.
            validation_errors = validate(parsed_data)

            if validation_errors:
                raise ValueError(
                    "AI вернул неполную структуру: "
                    + " ".join(validation_errors[:5])
                )

            usage = response.usage

            return {
                "data": parsed_data,
                "tokens_in": (
                    getattr(usage, "prompt_tokens", 0) or 0
                ),
                "tokens_out": (
                    getattr(usage, "completion_tokens", 0) or 0
                ),
            }

        except Exception as error:
            last_error = error

    raise ValueError(
        "AI дважды вернул неполную или некорректную структуру маршрута. "
        f"Последняя причина: {str(last_error)[:300]}"
    )




# ==========================================================
# AI-АНАЛИЗ БЮДЖЕТА ПОЕЗДКИ
# ==========================================================

BUDGET_ANALYSIS_SYSTEM_PROMPT = """Ты — финансовый помощник TravelMind.

Верни только один короткий валидный JSON-объект.
Не используй Markdown, комментарии или текст вне JSON.

Используй только цифры из контекста. Не выдумывай цены, скидки,
заведения, акции или фактические траты.

Строгий формат:
{
  "status": "safe|attention|over_budget|no_data",
  "summary": "Одно короткое предложение.",
  "recommendations": [
    {
      "priority": "low|medium|high",
      "title": "Короткий заголовок",
      "text": "Короткий практический совет."
    }
  ],
  "potential_saving_min": 0,
  "potential_saving_max": 0
}

Требования:
- Рекомендаций: от 2 до 3.
- Каждая рекомендация: не более 15 слов.
- summary: не более 20 слов.
- Если фактических трат нет, status должен быть no_data.
"""


def _number(value, default=0.0) -> float:
    """Безопасно приводит значение к числу."""
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return float(default)


def _build_budget_analysis_fallback(budget_context: dict) -> dict:
    """
    Формирует рекомендации без LLM.

    Используется, если модель вернула оборванный или неверный JSON.
    """
    total_budget = _number(budget_context.get("total_budget"))
    planned_total = _number(budget_context.get("planned_total"))
    actual_total = _number(budget_context.get("actual_total"))
    remaining_budget = _number(budget_context.get("remaining_budget"))
    used_percent = _number(budget_context.get("budget_used_percent"))
    manual_count = int(
        _number(budget_context.get("unplanned_expenses_count"))
    )
    manual_total = _number(
        budget_context.get("unplanned_actual_total")
    )
    currency = str(budget_context.get("currency") or "RUB")

    has_actual_data = actual_total > 0

    if not has_actual_data:
        status = "no_data"
        summary = (
            "Фактические расходы пока не внесены: анализ основан "
            "на запланированном бюджете."
        )
    elif remaining_budget < 0 or used_percent > 100:
        status = "over_budget"
        summary = (
            f"Бюджет превышен на {abs(remaining_budget):,.0f} {currency}."
        ).replace(",", " ")
    elif used_percent >= 75:
        status = "attention"
        summary = (
            f"Использовано {used_percent:.0f}% бюджета: "
            "контролируйте оставшиеся траты."
        )
    else:
        status = "safe"
        summary = (
            f"Использовано {used_percent:.0f}% бюджета. "
            "Расходы находятся под контролем."
        )

    recommendations = []

    if not has_actual_data:
        recommendations.append(
            {
                "priority": "medium",
                "title": "Вносите фактические траты",
                "text": (
                    "Указывайте реальные суммы после оплаты, "
                    "чтобы анализ был точнее."
                ),
            }
        )

        if planned_total > total_budget and total_budget > 0:
            recommendations.append(
                {
                    "priority": "high",
                    "title": "Сократите плановые расходы",
                    "text": (
                        "План превышает лимит. "
                        "Пересмотрите необязательные активности."
                    ),
                }
            )
        else:
            recommendations.append(
                {
                    "priority": "low",
                    "title": "Оставьте резерв",
                    "text": (
                        "Сохраните часть бюджета на непредвиденные "
                        "расходы и изменения планов."
                    ),
                }
            )

    if remaining_budget < 0:
        recommendations.append(
            {
                "priority": "high",
                "title": "Остановите необязательные траты",
                "text": (
                    "Откажитесь от спонтанных покупок и выберите "
                    "более бюджетные варианты досуга."
                ),
            }
        )
        recommendations.append(
            {
                "priority": "high",
                "title": "Проверьте транспорт",
                "text": (
                    "Сравните расходы на такси с общественным "
                    "транспортом и пешими маршрутами."
                ),
            }
        )

    elif used_percent >= 75:
        recommendations.append(
            {
                "priority": "medium",
                "title": "Установите дневной лимит",
                "text": (
                    "Разделите оставшийся бюджет на дни поездки "
                    "и придерживайтесь этой суммы."
                ),
            }
        )
        recommendations.append(
            {
                "priority": "medium",
                "title": "Контролируйте дополнительные покупки",
                "text": (
                    "Сначала оплачивайте обязательные расходы, "
                    "а покупки планируйте из остатка."
                ),
            }
        )

    elif has_actual_data:
        recommendations.append(
            {
                "priority": "low",
                "title": "Продолжайте учитывать траты",
                "text": (
                    "Регулярно сохраняйте фактические суммы, "
                    "чтобы вовремя заметить рост расходов."
                ),
            }
        )

    if manual_count > 0:
        recommendations.append(
            {
                "priority": "medium",
                "title": "Контролируйте внеплановые расходы",
                "text": (
                    f"Зафиксировано внеплановых трат: "
                    f"{manual_total:,.0f} {currency}."
                ).replace(",", " "),
            }
        )

    unique_recommendations = []
    seen_titles = set()

    for item in recommendations:
        if item["title"] not in seen_titles:
            unique_recommendations.append(item)
            seen_titles.add(item["title"])

    if len(unique_recommendations) < 2:
        unique_recommendations.append(
            {
                "priority": "low",
                "title": "Проверяйте остаток бюджета",
                "text": (
                    "Сверяйте запланированные и фактические суммы "
                    "после каждого дня поездки."
                ),
            }
        )

    potential_saving = 0.0

    if remaining_budget < 0:
        potential_saving = abs(remaining_budget)
    elif manual_total > 0:
        potential_saving = manual_total * 0.2

    return {
        "status": status,
        "summary": summary,
        "recommendations": unique_recommendations[:3],
        "potential_saving_min": round(potential_saving * 0.5, 2),
        "potential_saving_max": round(potential_saving, 2),
        "source": "local_fallback",
    }


def _normalize_budget_analysis(
    result: dict,
    budget_context: dict,
) -> dict:
    """Проверяет и приводит ответ AI к ожидаемой структуре."""
    fallback = _build_budget_analysis_fallback(budget_context)

    if not isinstance(result, dict):
        return fallback

    allowed_statuses = {
        "safe",
        "attention",
        "over_budget",
        "no_data",
    }

    status = str(result.get("status") or "").strip().lower()

    if status not in allowed_statuses:
        status = fallback["status"]

    summary = str(result.get("summary") or "").strip()

    if not summary:
        summary = fallback["summary"]

    recommendations = []
    raw_recommendations = result.get("recommendations")

    if isinstance(raw_recommendations, list):
        for item in raw_recommendations[:3]:
            if not isinstance(item, dict):
                continue

            priority = str(item.get("priority") or "low").lower()

            if priority not in {"low", "medium", "high"}:
                priority = "low"

            title = str(item.get("title") or "Рекомендация").strip()
            text = str(item.get("text") or "").strip()

            if text:
                recommendations.append(
                    {
                        "priority": priority,
                        "title": title,
                        "text": text,
                    }
                )

    if len(recommendations) < 2:
        recommendations = fallback["recommendations"]

    saving_min = _number(result.get("potential_saving_min"))
    saving_max = _number(result.get("potential_saving_max"))

    if saving_min < 0:
        saving_min = 0

    if saving_max < 0:
        saving_max = 0

    if saving_min == 0 and saving_max == 0:
        saving_min = fallback["potential_saving_min"]
        saving_max = fallback["potential_saving_max"]

    return {
        "status": status,
        "summary": summary,
        "recommendations": recommendations[:3],
        "potential_saving_min": round(saving_min, 2),
        "potential_saving_max": round(saving_max, 2),
        "source": "ai",
    }


def analyze_budget_with_ai(budget_context: dict) -> dict:
    """
    Анализирует бюджет через AI.

    При обрыве JSON выполняет повторную попытку.
    Если ответ AI снова некорректен, возвращает локальный анализ.
    """
    compact_context = json.dumps(
        budget_context,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    user_prompt = f"""Данные бюджета:
{compact_context}

Верни только короткий JSON строго по схеме из системной инструкции."""

    client = _create_llm_client()
    last_error = None

    for _ in range(2):
        try:
            response = client.chat.completions.create(
                model=st.secrets.get("LLM_MODEL", "deepseek-chat"),
                messages=[
                    {
                        "role": "system",
                        "content": BUDGET_ANALYSIS_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0.0,
                max_tokens=500,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            content = str(content or "").strip()

            if not content:
                raise ValueError("Провайдер вернул пустой ответ.")

            parsed_result = _parse_json(content)
            normalized_result = _normalize_budget_analysis(
                parsed_result,
                budget_context,
            )

            usage = response.usage

            return {
                "data": normalized_result,
                "tokens_in": getattr(usage, "prompt_tokens", 0) or 0,
                "tokens_out": getattr(usage, "completion_tokens", 0) or 0,
            }

        except Exception as error:
            last_error = error

    fallback_result = _build_budget_analysis_fallback(budget_context)

    return {
        "data": fallback_result,
        "tokens_in": 0,
        "tokens_out": 0,
        "warning": (
            "AI временно вернул неполный ответ. "
            f"Использован локальный анализ: {str(last_error)[:200]}"
        ),
    }


def validate(data: dict) -> list:
    """Базовая проверка структуры ответа. Возвращает список замечаний."""
    errors = []

    if not data.get("title"):
        errors.append("Модель не вернула название маршрута.")

    cover_profile = str(data.get("cover_profile", "")).strip().lower()

    if not cover_profile:
        errors.append("Модель не вернула профиль обложки маршрута.")
    elif cover_profile not in ALLOWED_COVER_PROFILES:
        errors.append(
            "Модель вернула недопустимый профиль обложки: "
            f"«{cover_profile}»."
        )

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
