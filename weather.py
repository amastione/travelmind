"""Получение и обработка прогноза погоды для TravelMind."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

import requests
import streamlit as st


GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"



# Прогноз Open-Meteo имеет ограниченный горизонт.
FORECAST_MAX_DAYS = 16

WEATHER_CODES = {
    0: {"title": "Ясно", "icon": "☀️", "outdoor": True},
    1: {"title": "Преимущественно ясно", "icon": "🌤️", "outdoor": True},
    2: {"title": "Переменная облачность", "icon": "⛅", "outdoor": True},
    3: {"title": "Пасмурно", "icon": "☁️", "outdoor": True},
    45: {"title": "Туман", "icon": "🌫️", "outdoor": False},
    48: {"title": "Туман с изморозью", "icon": "🌫️", "outdoor": False},
    51: {"title": "Слабая морось", "icon": "🌦️", "outdoor": True},
    53: {"title": "Морось", "icon": "🌦️", "outdoor": False},
    55: {"title": "Сильная морось", "icon": "🌧️", "outdoor": False},
    56: {"title": "Ледяная морось", "icon": "🌧️", "outdoor": False},
    57: {"title": "Сильная ледяная морось", "icon": "🌧️", "outdoor": False},
    61: {"title": "Небольшой дождь", "icon": "🌦️", "outdoor": True},
    63: {"title": "Дождь", "icon": "🌧️", "outdoor": False},
    65: {"title": "Сильный дождь", "icon": "🌧️", "outdoor": False},
    66: {"title": "Ледяной дождь", "icon": "🌧️", "outdoor": False},
    67: {"title": "Сильный ледяной дождь", "icon": "🌧️", "outdoor": False},
    71: {"title": "Слабый снег", "icon": "🌨️", "outdoor": True},
    73: {"title": "Снег", "icon": "🌨️", "outdoor": False},
    75: {"title": "Сильный снег", "icon": "❄️", "outdoor": False},
    77: {"title": "Снежные зёрна", "icon": "🌨️", "outdoor": False},
    80: {"title": "Ливневый дождь", "icon": "🌦️", "outdoor": False},
    81: {"title": "Ливень", "icon": "🌧️", "outdoor": False},
    82: {"title": "Сильный ливень", "icon": "⛈️", "outdoor": False},
    85: {"title": "Слабый снегопад", "icon": "🌨️", "outdoor": False},
    86: {"title": "Сильный снегопад", "icon": "❄️", "outdoor": False},
    95: {"title": "Гроза", "icon": "⛈️", "outdoor": False},
    96: {"title": "Гроза с градом", "icon": "⛈️", "outdoor": False},
    99: {"title": "Сильная гроза с градом", "icon": "⛈️", "outdoor": False},
}


def _as_float(value: Any, default: float = 0.0) -> float:
    """Безопасно приводит значение к float."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def get_weather_label(weather_code: int | None) -> dict[str, Any]:
    """Возвращает описание погодного кода WMO."""
    return WEATHER_CODES.get(
        weather_code,
        {
            "title": "Нет точного описания",
            "icon": "🌡️",
            "outdoor": True,
        },
    )


def _destination_search_variants(destination: str) -> list[str]:
    """
    Создаёт варианты запроса для Open-Meteo.

    DaData возвращает точную полную запись:
    «Ставрополь, Ставропольский край, Россия».

    Однако Open-Meteo обычно лучше находит именно населённый пункт:
    «Ставрополь».
    """
    full_name = " ".join(str(destination or "").split())

    if not full_name:
        return []

    variants = [full_name]

    # Первый элемент в записи DaData — город, посёлок или регион.
    # «Ставрополь, Ставропольский край, Россия» → «Ставрополь».
    first_part = full_name.split(",", 1)[0].strip()

    if first_part and first_part.casefold() != full_name.casefold():
        variants.append(first_part)

    # Open-Meteo иногда не находит населённые пункты вместе с типом:
    # «пгт Каменномостский» → «Каменномостский»,
    # «село Архыз» → «Архыз».
    locality_prefixes = (
        "г. ",
        "город ",
        "пгт ",
        "посёлок ",
        "поселок ",
        "село ",
        "деревня ",
        "станица ",
        "хутор ",
    )

    short_name = first_part.casefold()

    for prefix in locality_prefixes:
        if short_name.startswith(prefix):
            without_prefix = first_part[len(prefix):].strip()

            if without_prefix:
                variants.append(without_prefix)

            break

    # Удаляем повторы, сохраняя исходный порядок.
    unique_variants = []
    seen = set()

    for variant in variants:
        normalized = variant.casefold()

        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_variants.append(variant)

    return unique_variants

def _osm_search_variants(destination: str) -> list[str]:
    """
    Передаёт геокодеру исходное название с контекстом.

    Не подставляет произвольные регионы и страны,
    не меняет название географического объекта.
    """
    query = " ".join(str(destination or "").split())

    return [query] if query else []


def _build_osm_place_name(
    place: dict[str, Any],
    fallback_name: str,
) -> str:
    """
    Формирует понятное короткое название места из ответа OpenStreetMap.
    """
    display_name = str(place.get("display_name") or "").strip()

    if not display_name:
        return fallback_name

    # Не показываем пользователю слишком длинную техническую строку.
    # Например:
    # «Чегемские водопады, Хушто-Сырт, Чегемский район,
    # Кабардино-Балкария, Россия»
    # оставляем первые три значимые части.
    parts = [
        part.strip()
        for part in display_name.split(",")
        if part.strip()
    ]

    return ", ".join(parts[:3]) or fallback_name


def _geocode_place_with_osm(
    destination: str,
) -> dict[str, Any] | None:
    """
    Ищет природный объект или достопримечательность через OpenStreetMap.

    Nominatim полезен там, где Open-Meteo не находит объект:
    водопады, ущелья, озёра, национальные парки, смотровые площадки.
    """
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": destination,
                "format": "jsonv2",
                "limit": 5,
                "addressdetails": 1,
                "accept-language": "ru",
            },
            headers={
                # Nominatim требует осмысленный User-Agent.
                "User-Agent": (
                    "TravelMind/1.0 "
                    "(educational travel planning application)"
                ),
            },
            timeout=12,
        )
        response.raise_for_status()
        results = response.json()

    except (requests.RequestException, ValueError):
        # Если OSM временно недоступен, не ломаем весь раздел погоды.
        # Основной поиск Open-Meteo уже был выполнен выше.
        return None

    if not isinstance(results, list):
        return None

    for place in results:
        if not isinstance(place, dict):
            continue

        try:
            latitude = float(place.get("lat"))
            longitude = float(place.get("lon"))
        except (TypeError, ValueError):
            continue

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue
        
        address = place.get("address")

        if not isinstance(address, dict):
            address = {}
        return {
            "name": _build_osm_place_name(
                place,
                fallback_name=destination,
            ),
            "country": str(address.get("country") or ""),
            "admin1": str(address.get("state") or ""),
            "latitude": latitude,
            "longitude": longitude,
            # Для Open-Meteo подходит auto: часовой пояс определяется
            # по найденным координатам достопримечательности.
            "timezone": "auto",
            "source": "openstreetmap",
        }

    return None

@st.cache_data(ttl=24 * 3600, show_spinner=False)
def geocode_destination(destination: str) -> dict[str, Any] | None:
    """
    Ищет координаты направления для прогноза погоды.

    Порядок поиска:
    1. Open-Meteo Geocoding — города, посёлки, регионы.
    2. OpenStreetMap Nominatim — водопады, ущелья, озёра,
       парки и другие достопримечательности.
    """
    destination = " ".join(str(destination or "").split())

    if not destination:
        raise ValueError(
            "В поиск погоды передано пустое направление. "
            "Нужно проверить поле направления во вкладке погоды."
        )

    search_variants = _destination_search_variants(destination)

    # ------------------------------------------------------
    # 1. Ищем населённый пункт через Open-Meteo.
    # ------------------------------------------------------
    for search_query in search_variants:
        try:
            response = requests.get(
                GEOCODING_URL,
                params={
                    "name": search_query,
                    "count": 5,
                    "language": "ru",
                    "format": "json",
                },
                timeout=10,
            )
            response.raise_for_status()

        except requests.RequestException:
            # Ошибка одного провайдера не должна блокировать
            # дальнейший поиск через Nominatim.
            continue

        try:
            payload = response.json()
        except ValueError:
            continue
        

        if not isinstance(payload, dict) or payload.get("error"):
            continue

        results = payload.get("results") or []

        for place in results:
            if not isinstance(place, dict):
                continue

            try:
                latitude = float(place["latitude"])
                longitude = float(place["longitude"])
            except (KeyError, TypeError, ValueError):
                continue

            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                continue

            return {
                "name": str(place.get("name") or search_query),
                "country": str(place.get("country") or ""),
                "admin1": str(place.get("admin1") or ""),
                "latitude": latitude,
                "longitude": longitude,
                "timezone": str(place.get("timezone") or "auto"),
                "source": "open_meteo",
            }

    # ------------------------------------------------------
    # 2. Если город не найден — ищем конкретный объект на OSM.
    # ------------------------------------------------------
    # Для природных объектов используем расширенный список вариантов:
    # сокращения регионов, полные названия субъектов, название без региона,
    # а также возможное название ближайшего населённого пункта.
    # Nominatim получает исходное название вместе с регионом
    # и страной, без искусственно придуманных вариантов.
    osm_queries = _osm_search_variants(destination)

    seen_queries = set()

    for query in osm_queries:
        normalized_query = query.casefold()

        if not normalized_query or normalized_query in seen_queries:
            continue

        seen_queries.add(normalized_query)

        osm_place = _geocode_place_with_osm(query)

        if osm_place:
            return osm_place

    return None

@st.cache_data(ttl=24 * 3600, show_spinner=False)
def search_destinations(query: str) -> list[dict[str, Any]]:
    """
    Возвращает до 5 вариантов населённых пунктов для выбора пользователем.

    Используется только текст поискового запроса. Бюджет, интересы,
    маршрут и данные пользователя во внешний сервис не передаются.
    """
    query = " ".join(str(query or "").split())

    if len(query) < 3:
        return []

    try:
        response = requests.get(
            GEOCODING_URL,
            params={
                "name": query,
                "count": 5,
                "language": "ru",
                "format": "json",
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return []

    results = payload.get("results") or []

    destinations = []

    for place in results:
        if not isinstance(place, dict):
            continue

        try:
            latitude = float(place["latitude"])
            longitude = float(place["longitude"])
        except (KeyError, TypeError, ValueError):
            continue

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue

        city_name = str(place.get("name") or "").strip()
        country = str(place.get("country") or "").strip()
        region = str(place.get("admin1") or "").strip()

        if not city_name:
            continue

        label_parts = [city_name]

        if region and region.lower() != city_name.lower():
            label_parts.append(region)

        if country:
            label_parts.append(country)

        destinations.append(
            {
                "label": ", ".join(label_parts),
                "city": city_name,
                "country": country,
                "region": region,
                "latitude": latitude,
                "longitude": longitude,
                "timezone": str(place.get("timezone") or "auto"),
            }
        )

    return destinations

@st.cache_data(ttl=3 * 3600, show_spinner=False)
def get_weather_forecast(
    latitude: float,
    longitude: float,
    timezone: str = "auto",
) -> dict[str, Any]:
    """
    Получает дневной и почасовой прогноз.

    Данные кэшируются на 3 часа, чтобы:
    - не создавать лишние запросы;
    - не замедлять страницу;
    - не зависеть от Weather API при каждом открытии маршрута.
    """
    response = requests.get(
        FORECAST_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone or "auto",
            "forecast_days": FORECAST_MAX_DAYS,
            "wind_speed_unit": "ms",
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "apparent_temperature_max,"
                "apparent_temperature_min,"
                "precipitation_probability_max,"
                "precipitation_sum,"
                "wind_speed_10m_max"
            ),
            "hourly": (
                "temperature_2m,"
                "apparent_temperature,"
                "precipitation_probability,"
                "precipitation,"
                "weather_code,"
                "wind_speed_10m"
            ),
        },
        timeout=12,
    )
    response.raise_for_status()

    return response.json()


def build_daily_weather(
    raw_forecast: dict[str, Any],
    start_date: str,
    end_date: str,
) -> list[dict[str, Any]]:
    """Преобразует JSON Open-Meteo в компактный прогноз по дням поездки."""
    daily = raw_forecast.get("daily") or {}

    dates = daily.get("time") or []
    codes = daily.get("weather_code") or []
    temp_max = daily.get("temperature_2m_max") or []
    temp_min = daily.get("temperature_2m_min") or []
    feels_max = daily.get("apparent_temperature_max") or []
    feels_min = daily.get("apparent_temperature_min") or []
    rain_probability = daily.get("precipitation_probability_max") or []
    precipitation_sum = daily.get("precipitation_sum") or []
    wind_max = daily.get("wind_speed_10m_max") or []

    result = []

    for index, day_date in enumerate(dates):
        if not (start_date <= str(day_date) <= end_date):
            continue

        code = int(_as_float(codes[index] if index < len(codes) else 0))
        meta = get_weather_label(code)

        item = {
            "date": str(day_date),
            "weather_code": code,
            "condition": meta["title"],
            "icon": meta["icon"],
            "is_outdoor_friendly": bool(meta["outdoor"]),
            "temp_min": round(
                _as_float(temp_min[index] if index < len(temp_min) else 0),
                1,
            ),
            "temp_max": round(
                _as_float(temp_max[index] if index < len(temp_max) else 0),
                1,
            ),
            "feels_min": round(
                _as_float(feels_min[index] if index < len(feels_min) else 0),
                1,
            ),
            "feels_max": round(
                _as_float(feels_max[index] if index < len(feels_max) else 0),
                1,
            ),
            "rain_probability": int(
                _as_float(
                    rain_probability[index]
                    if index < len(rain_probability)
                    else 0
                )
            ),
            "precipitation_mm": round(
                _as_float(
                    precipitation_sum[index]
                    if index < len(precipitation_sum)
                    else 0
                ),
                1,
            ),
            "wind_max": round(
                _as_float(
                    wind_max[index] if index < len(wind_max) else 0
                ),
                1,
            ),
        }

        item["warnings"] = build_weather_warnings(item)
        item["clothing_tip"] = build_clothing_tip(item)

        result.append(item)

    return result


def build_weather_warnings(day: dict[str, Any]) -> list[str]:
    """Формирует предупреждения на основе подтверждённых данных API."""
    warnings = []

    if day.get("weather_code") in {80, 81, 82, 95, 96, 99}:
        warnings.append("Интенсивные осадки могут нарушить прогулки на улице.")

    elif (
        _as_float(day.get("rain_probability")) >= 70
        or _as_float(day.get("precipitation_mm")) >= 5
    ):
        warnings.append("Высока вероятность осадков: предусмотрите крытые места.")

    if _as_float(day.get("wind_max")) >= 12:
        warnings.append("Ожидается сильный ветер: будьте осторожны у воды и на высоте.")

    if _as_float(day.get("temp_max")) >= 30:
        warnings.append("Ожидается жара: планируйте прогулки утром и вечером.")

    if _as_float(day.get("temp_min")) <= 0:
        warnings.append("Температура может опускаться до нуля или ниже.")

    return warnings


def build_clothing_tip(day: dict[str, Any]) -> str:
    """Возвращает короткий совет по одежде без обращения к AI."""
    temp_min = _as_float(day.get("temp_min"))
    temp_max = _as_float(day.get("temp_max"))
    rain_probability = _as_float(day.get("rain_probability"))
    wind_max = _as_float(day.get("wind_max"))

    tips = []

    if temp_max >= 28:
        tips.append("лёгкая одежда, головной убор и вода")
    elif temp_max >= 18:
        tips.append("лёгкая одежда и слой на вечер")
    elif temp_max >= 8:
        tips.append("куртка или тёплый свитер")
    else:
        tips.append("тёплая верхняя одежда")

    if rain_probability >= 50:
        tips.append("зонт или непромокаемая куртка")

    if wind_max >= 10:
        tips.append("ветрозащитный слой")

    if temp_min <= 2:
        tips.append("тёплая обувь")

    return "Рекомендуется: " + ", ".join(tips) + "."


def get_hourly_weather_for_day(
    raw_forecast: dict[str, Any],
    target_date: str,
    hours: set[int] | None = None,
) -> list[dict[str, Any]]:
    """
    Возвращает почасовую погоду для одного дня.

    Если hours передан, возвращаются только нужные часы,
    например часы активностей маршрута.
    """
    hourly = raw_forecast.get("hourly") or {}

    times = hourly.get("time") or []
    temperatures = hourly.get("temperature_2m") or []
    feels_like = hourly.get("apparent_temperature") or []
    rain_probability = hourly.get("precipitation_probability") or []
    precipitation = hourly.get("precipitation") or []
    weather_codes = hourly.get("weather_code") or []
    wind_speed = hourly.get("wind_speed_10m") or []

    result = []

    for index, raw_time in enumerate(times):
        raw_time = str(raw_time)

        if not raw_time.startswith(target_date):
            continue

        try:
            hour = int(raw_time[11:13])
        except (TypeError, ValueError):
            continue

        if hours and hour not in hours:
            continue

        code = int(
            _as_float(
                weather_codes[index] if index < len(weather_codes) else 0
            )
        )
        meta = get_weather_label(code)

        result.append(
            {
                "time": raw_time,
                "hour": hour,
                "icon": meta["icon"],
                "condition": meta["title"],
                "temp": round(
                    _as_float(
                        temperatures[index]
                        if index < len(temperatures)
                        else 0
                    ),
                    1,
                ),
                "feels_like": round(
                    _as_float(
                        feels_like[index]
                        if index < len(feels_like)
                        else 0
                    ),
                    1,
                ),
                "rain_probability": int(
                    _as_float(
                        rain_probability[index]
                        if index < len(rain_probability)
                        else 0
                    )
                ),
                "precipitation_mm": round(
                    _as_float(
                        precipitation[index]
                        if index < len(precipitation)
                        else 0
                    ),
                    1,
                ),
                "wind": round(
                    _as_float(
                        wind_speed[index]
                        if index < len(wind_speed)
                        else 0
                    ),
                    1,
                ),
            }
        )

    return result


def is_forecast_available(
    trip_start: str,
    available_weather: list[dict[str, Any]],
) -> bool:
    """Проверяет, есть ли прогноз хотя бы на дату начала поездки."""
    return any(item.get("date") == trip_start for item in available_weather)


def build_ai_weather_context(
    weather_days: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Возвращает компактные проверенные данные для AI.

    Не передаём модели полный ответ Weather API, лишние поля,
    координаты, персональные данные или технические метаданные.
    """
    result = []

    for day in weather_days:
        result.append(
            {
                "date": day.get("date"),
                "condition": day.get("condition"),
                "temp_min": day.get("temp_min"),
                "temp_max": day.get("temp_max"),
                "rain_probability": day.get("rain_probability"),
                "precipitation_mm": day.get("precipitation_mm"),
                "wind_max": day.get("wind_max"),
                "warnings": day.get("warnings") or [],
            }
        )

    return result
# ==========================================================
# ПОГОДА ДЛЯ ТОЧКИ, УКАЗАННОЙ В AI-МАРШРУТЕ
# ==========================================================

def resolve_route_weather_location(
    route_data: dict[str, Any] | None,
    trip_destination: str,
) -> dict[str, Any] | None:
    """
    Определяет точку прогноза по данным маршрута.

    Сначала ищет основную точку из route_data["weather"].
    Если она не найдена — ищет направление самой поездки.

    Координаты, придуманные AI, автоматически не используются.
    """
    route = route_data if isinstance(route_data, dict) else {}

    weather_settings = route.get("weather")

    if not isinstance(weather_settings, dict):
        weather_settings = {}

    primary_location = " ".join(
        str(weather_settings.get("primary_location") or "").split()
    )

    location_hint = " ".join(
        str(weather_settings.get("location_hint") or "").split()
    )

    terrain_note = str(
        weather_settings.get("terrain_note") or ""
    ).strip()

    destination = " ".join(
        str(trip_destination or "").split()
    )

    candidates = []

    if primary_location:
        # Сохраняем региональный контекст, если он есть.
        query = primary_location

        if (
            location_hint
            and location_hint.casefold() not in query.casefold()
        ):
            query = f"{query}, {location_hint}"

        candidates.append((query, "route_primary_location"))

    if destination:
        candidates.append((destination, "trip_destination_fallback"))

    seen = set()

    for query, selection_source in candidates:
        query_key = query.casefold()

        if query_key in seen:
            continue

        seen.add(query_key)

        location = geocode_destination(query)

        if not location:
            continue

        # Не изменяем исходный результат геокодера.
        resolved_location = dict(location)

        resolved_location["coordinates_source"] = "geocoder"
        resolved_location["selection_source"] = selection_source
        resolved_location["weather_query"] = query
        resolved_location["terrain_note"] = terrain_note

        return resolved_location

    return None


def get_route_weather_forecast(
    route_data: dict[str, Any] | None,
    trip_destination: str,
) -> dict[str, Any] | None:
    """
    Получает прогноз для основной точки маршрута.

    None означает, что точку определить не удалось.
    Ошибки запроса прогноза передаются вызывающему коду.
    """
    location = resolve_route_weather_location(
        route_data=route_data,
        trip_destination=trip_destination,
    )

    if location is None:
        return None

    raw_forecast = get_weather_forecast(
        latitude=location["latitude"],
        longitude=location["longitude"],
        timezone=str(location.get("timezone") or "auto"),
    )

    return {
        "location": location,
        "raw_forecast": raw_forecast,
    }
