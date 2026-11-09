"""Получение справочной информации о месте из русской Wikipedia."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import streamlit as st


WIKIPEDIA_API_URL = "https://ru.wikipedia.org/w/api.php"

# Важно указывать User-Agent при запросах к Wikimedia.
USER_AGENT = (
    "TravelMind/1.0 "
    "(educational travel planner; contact: travelmind-project)"
)


def _clean_text(value: object) -> str:
    """Очищает текст от лишних пробелов."""
    return " ".join(str(value or "").split()).strip()


def _shorten_text(text: str, max_length: int = 850) -> str:
    """
    Ограничивает длину справки, стараясь завершить её целым предложением.
    """
    text = _clean_text(text)

    if len(text) <= max_length:
        return text

    shortened = text[:max_length].rsplit(".", 1)[0].strip()

    if len(shortened) < 180:
        shortened = text[:max_length].rsplit(" ", 1)[0].strip()

    return f"{shortened}…"


def _request_wikipedia(params: dict) -> dict:
    """Выполняет GET-запрос к MediaWiki API."""
    query_params = {
        "format": "json",
        "formatversion": "2",
        **params,
    }

    request_url = (
        f"{WIKIPEDIA_API_URL}?{urlencode(query_params)}"
    )

    request = Request(
        request_url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    with urlopen(request, timeout=8) as response:
        payload = response.read().decode("utf-8")

    result = json.loads(payload)

    if not isinstance(result, dict):
        raise ValueError("Wikipedia вернула неожиданный формат ответа.")

    return result


def _find_article_title(query: str) -> str:
    """
    Ищет наиболее подходящую статью русской Wikipedia
    и возвращает её точное название.
    """
    clean_query = _clean_text(query)

    if not clean_query:
        return ""

    result = _request_wikipedia(
        {
            "action": "query",
            "list": "search",
            "srsearch": clean_query,
            "srnamespace": "0",
            "srlimit": "1",
        }
    )

    search_items = (
        result.get("query", {}).get("search", [])
    )

    if not isinstance(search_items, list) or not search_items:
        return ""

    first_item = search_items[0]

    if not isinstance(first_item, dict):
        return ""

    return _clean_text(first_item.get("title"))


def _get_article_extract(title: str) -> dict | None:
    """
    Получает краткое вступление статьи по её точному названию.
    """
    if not title:
        return None

    result = _request_wikipedia(
        {
            "action": "query",
            "prop": "extracts|info",
            "titles": title,
            "exintro": "1",
            "explaintext": "1",
            "inprop": "url",
            "redirects": "1",
        }
    )

    pages = result.get("query", {}).get("pages", [])

    if not isinstance(pages, list) or not pages:
        return None

    page = pages[0]

    if not isinstance(page, dict) or page.get("missing"):
        return None

    article_title = _clean_text(page.get("title"))
    extract = _clean_text(page.get("extract"))
    full_url = _clean_text(page.get("fullurl"))

    if not article_title or not extract:
        return None

    if not full_url:
        full_url = (
            "https://ru.wikipedia.org/wiki/"
            + article_title.replace(" ", "_")
        )

    return {
        "title": article_title,
        "summary": _shorten_text(extract),
        "source_name": "Русская Wikipedia",
        "source_url": full_url,
        "retrieved_at": datetime.now(timezone.utc).strftime(
            "%d.%m.%Y %H:%M UTC"
        ),
    }


@st.cache_data(ttl=7 * 24 * 3600, show_spinner=False)
def get_historical_reference(
    primary_location: str,
    location_hint: str,
    trip_destination: str,
) -> dict | None:
    """
    Получает справку о главной точке маршрута.

    Приоритет поиска:
    1. Основная точка маршрута + регион.
    2. Основная точка маршрута.
    3. Общее направление поездки.

    Возвращает текст строго из Wikipedia без генерации AI.
    """
    primary_location = _clean_text(primary_location)
    location_hint = _clean_text(location_hint)
    trip_destination = _clean_text(trip_destination)

    search_queries = []

    if primary_location and location_hint:
        search_queries.append(
            f"{primary_location}, {location_hint}"
        )

    if primary_location:
        search_queries.append(primary_location)

    if trip_destination:
        search_queries.append(trip_destination)

    checked_queries = set()

    for query in search_queries:
        normalized_query = query.casefold()

        if not query or normalized_query in checked_queries:
            continue

        checked_queries.add(normalized_query)

        try:
            article_title = _find_article_title(query)
            article_data = _get_article_extract(article_title)

            if article_data:
                article_data["query_used"] = query
                return article_data

        except Exception:
            # Внешняя справка не должна мешать открытию маршрута.
            continue

    return None
