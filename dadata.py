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

        # Ищем не только города, но и субъекты / регионы.
        # Например, «Ингушетия» является регионом, а не городом.
        "from_bound": {"value": "region"},
        "to_bound": {"value": "city"},
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
        region = str(data.get("region_with_type") or "").strip()
        country = str(data.get("country") or "Россия").strip()

        # Для города используем city.
        # Для республики, области или края используем region.
        destination_name = city or region

        if not destination_name:
            continue

        # Тип направления нужен лишь для понятного интерфейса.
        destination_type = "город" if city else "регион"

        label_parts = [destination_name]

        # Для города добавляем регион.
        # Для самого региона повторять его второй раз не нужно.
        if city and region and region.casefold() != city.casefold():
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
                "region": region,
                "country": country,
                "type": destination_type,
                "raw_value": str(suggestion.get("value") or "").strip(),
                "latitude": latitude,
                "longitude": longitude,
                "fias_id": data.get("fias_id"),
            }
        )

    # Города показываем выше регионов, если совпадают оба типа.
    results.sort(
        key=lambda item: (
            item["type"] != "город",
            item["label"].casefold(),
        )
    )

    return results[:5]

    return results
