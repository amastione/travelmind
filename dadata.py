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
    Ищет города через DaData.

    Показываются только результаты типа «город».
    Если ничего не найдено, пользователь всё равно может оставить
    направление, введённое вручную.
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
        # Важно: запрашиваем именно города,
        # а не деревни, улицы, дома или организации.
        "from_bound": {"value": "city"},
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
    seen_values = set()

    for suggestion in raw_suggestions:
        if not isinstance(suggestion, dict):
            continue

        data = suggestion.get("data") or {}

        # DaData возвращает нормализованную строку, например:
        # «г Грозный, Респ Чеченская»
        full_value = str(suggestion.get("value") or "").strip()

        city = str(data.get("city") or "").strip()
        region = str(data.get("region_with_type") or "").strip()
        country = str(data.get("country") or "Россия").strip()

        # Дополнительная защита: принимаем только результаты,
        # где DaData действительно определила город.
        if not city:
            continue

        label_parts = [city]

        if region and region.casefold() != city.casefold():
            label_parts.append(region)

        if country:
            label_parts.append(country)

        label = ", ".join(label_parts)
        normalized_label = label.casefold()

        if normalized_label in seen_values:
            continue

        seen_values.add(normalized_label)

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
                # Именно эта строка подставится в поле направления.
                "label": label,
                "city": city,
                "region": region,
                "country": country,
                "raw_value": full_value,
                "latitude": latitude,
                "longitude": longitude,
                "fias_id": data.get("fias_id"),
            }
        )

    return results
