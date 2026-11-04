"""Работа с API подсказок DaData для поиска городов."""

from typing import Any

import requests
import streamlit as st


DADATA_SUGGEST_URL = (
    "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/address"
)


@st.cache_data(ttl=24 * 60 * 60, show_spinner=False)
def search_cities(query: str) -> list[dict[str, Any]]:
    """
    Ищет туристические направления через DaData.

    Поддерживаются:
    - города: Грозный, Казань, Москва;
    - регионы: Ингушетия, Карелия, Алтай, Камчатский край.

    Если ничего не найдено, пользователь всё равно может использовать
    текст, введённый вручную.
    """
    query = " ".join(str(query or "").split())

    if len(query) < 3:
        return []

    api_key = st.secrets.get("DADATA_API_KEY", "")

    if not api_key:
        return []

    headers = {
        "Authorization": f"Token {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "query": query,
        "count": 5,

        # Ищем регионы, города, посёлки, пгт и сёла.
        "from_bound": {"value": "region"},
        "to_bound": {"value": "settlement"},
    }

    try:
        response = requests.post(
            DADATA_SUGGEST_URL,
            headers=headers,
            json=payload,
            timeout=8,
        )
        response.raise_for_status()

        raw_suggestions = response.json().get("suggestions", [])

    except (requests.RequestException, ValueError):
        return []

    results = []
    seen_labels = set()

    for suggestion in raw_suggestions:
        if not isinstance(suggestion, dict):
            continue

        data = suggestion.get("data") or {}

        city = str(data.get("city") or "").strip()

        # Для посёлков, пгт, сёл и станиц DaData использует settlement.
        settlement = str(data.get("settlement") or "").strip()
        settlement_with_type = str(
            data.get("settlement_with_type") or ""
        ).strip()
        
        region = str(data.get("region_with_type") or "").strip()
        country = str(data.get("country") or "Россия").strip()
        
        # Приоритет:
        # 1. город;
        # 2. населённый пункт: посёлок / пгт / село / станица;
        # 3. регион.
        destination_name = city or settlement or region

        if not destination_name:
            continue

        # Тип направления нужен лишь для понятного интерфейса.
        if city:
            destination_type = "город"
        elif settlement:
            destination_type = "населённый пункт"
        else:
            destination_type = "регион"

        # Для посёлка показываем тип: «пгт Каменномостский»,
        # а не просто «Каменномостский».
        display_name = (
            settlement_with_type
            if settlement and not city and settlement_with_type
            else destination_name
        )
        
        label_parts = [display_name]
        
        if region and region.casefold() != destination_name.casefold():
            label_parts.append(region)
        
        if country:
            label_parts.append(country)

        label = ", ".join(label_parts)
        normalized_label = label.casefold()

        if normalized_label in seen_labels:
            continue

        seen_labels.add(normalized_label)

        latitude = data.get("geo_lat")
        longitude = data.get("geo_lon")

        try:
            latitude = float(latitude) if latitude else None
            longitude = float(longitude) if longitude else None
        except (TypeError, ValueError):
            latitude = None
            longitude = None

        results.append(
            {
                "label": label,
                "city": city,
                "settlement": settlement,
                "region": region,
                "country": country,
                "type": destination_type,
                "raw_value": str(suggestion.get("value") or "").strip(),
                "latitude": latitude,
                "longitude": longitude,
                "fias_id": data.get("fias_id"),
            }
        )

    # Точные совпадения должны быть выше частичных.
    # Например, по запросу «Дагестан» выше будут:
    # «Республика Дагестан, Россия»,
    # а не «Дагестанские Огни».
    normalized_query = query.casefold()

    type_priority = {
        "регион": 0,
        "город": 1,
        "населённый пункт": 2,
    }

    def sort_key(item):
        destination_name = (
            item["city"]
            or item["settlement"]
            or item["region"]
        ).casefold()

        is_exact_match = destination_name == normalized_query
        starts_with_query = destination_name.startswith(normalized_query)

        return (
            0 if is_exact_match else 1,
            0 if starts_with_query else 1,
            type_priority.get(item["type"], 9),
            item["label"].casefold(),
        )

    results.sort(key=sort_key)

    return results[:5]

    return results
