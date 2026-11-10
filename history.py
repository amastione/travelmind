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

# Такие статьи обычно не являются справкой о городе, регионе,
# природном объекте или достопримечательности.
UNSUITABLE_TITLE_WORDS = {
    "мвд",
    "управление",
    "главное управление",
    "администрация",
    "министерство",
    "департамент",
    "комитет",
    "служба",
    "отдел",
    "прокуратура",
    "суд",
    "полиция",
    "университет",
    "институт",
    "академия",
    "колледж",
    "школа",
    "больница",
    "банк",
    "компания",
    "предприятие",
    "футбольный клуб",
    "хоккейный клуб",
    "аэропорт",
    "вокзал",
}


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


def _normalize_place_name(value: str) -> str:
    """
    Нормализует название для сравнения.

    Примеры:
    «г. Краснодар» → «краснодар»
    «город Санкт-Петербург» → «санкт-петербург»
    """
    value = _clean_text(value).casefold()

    value = re.sub(
        r"^(г\.?|город|пос\.?|посёлок|поселок|пгт\.?|с\.?|село|"
        r"ст\.?|станица|дер\.?|деревня)\s+",
        "",
        value,
        flags=re.IGNORECASE,
    )

    return value.strip(" ,.")


def _is_unsuitable_article_title(title: str) -> bool:
    """
    Отсекает статьи об учреждениях и организациях.

    Важно: этот фильтр используется только при поиске. Точная статья,
    указанная пользователем, имеет более высокий приоритет.
    """
    normalized_title = _normalize_place_name(title)

    return any(
        blocked_word in normalized_title
        for blocked_word in UNSUITABLE_TITLE_WORDS
    )


def _get_article_extract(title: str) -> dict | None:
    """
    Получает краткое вступление статьи по её точному названию.
    """
    title = _clean_text(title)

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


def _get_exact_article(query: str) -> dict | None:
    """
    Сначала пытается найти статью с точным названием места.

    Например:
    «Санкт-Петербург» → статья «Санкт-Петербург»,
    а не «Главное управление МВД России по городу Санкт-Петербургу...».
    """
    query = _clean_text(query)

    if not query:
        return None

    article_data = _get_article_extract(query)

    if not article_data:
        return None

    normalized_query = _normalize_place_name(query)
    normalized_title = _normalize_place_name(
        article_data.get("title", "")
    )

    # Разрешаем точное совпадение и редирект Wikipedia.
    if normalized_query == normalized_title:
        return article_data

    return None


def _find_article_titles(query: str) -> list[str]:
    """
    Ищет несколько подходящих статей русской Wikipedia.

    Первый результат больше не выбирается автоматически:
    он может относиться к МВД, университету или другой организации.
    """
    clean_query = _clean_text(query)

    if not clean_query:
        return []

    result = _request_wikipedia(
        {
            "action": "query",
            "list": "search",
            "srsearch": clean_query,
            "srnamespace": "0",
            "srlimit": "10",
        }
    )

    search_items = (
        result.get("query", {}).get("search", [])
    )

    if not isinstance(search_items, list):
        return []

    normalized_query = _normalize_place_name(clean_query)

    suitable_titles = []
    exact_titles = []

    for item in search_items:
        if not isinstance(item, dict):
            continue

        title = _clean_text(item.get("title"))

        if not title:
            continue

        if _is_unsuitable_article_title(title):
            continue

        normalized_title = _normalize_place_name(title)

        # Точные совпадения всегда идут первыми.
        if normalized_title == normalized_query:
            exact_titles.append(title)
        else:
            suitable_titles.append(title)

    return exact_titles + suitable_titles


@st.cache_data(ttl=7 * 24 * 3600, show_spinner=False)
def get_historical_reference(
    primary_location: str,
    location_hint: str,
    trip_destination: str,
) -> dict | None:
    """
    Получает справку о главной точке маршрута.

    Приоритет:
    1. Точная статья о главной точке маршрута.
    2. Точная статья об общем направлении поездки.
    3. Поиск по главной точке и региону.
    4. Поиск по главной точке.
    5. Поиск по общему направлению поездки.

    Текст берётся строго из Wikipedia, без генерации AI.
    """
    primary_location = _clean_text(primary_location)
    location_hint = _clean_text(location_hint)
    trip_destination = _clean_text(trip_destination)

    # ------------------------------------------------------
    # Шаг 1. Приоритетный поиск точной статьи.
    # ------------------------------------------------------
    exact_candidates = [
        primary_location,
        trip_destination,
    ]

    checked_exact = set()

    for candidate in exact_candidates:
        normalized_candidate = _normalize_place_name(candidate)

        if (
            not candidate
            or not normalized_candidate
            or normalized_candidate in checked_exact
        ):
            continue

        checked_exact.add(normalized_candidate)

        try:
            article_data = _get_exact_article(candidate)

            if article_data:
                article_data["query_used"] = candidate
                article_data["match_type"] = "exact_title"
                return article_data

        except Exception:
            # Внешняя справка не должна мешать открытию маршрута.
            continue

    # ------------------------------------------------------
    # Шаг 2. Резервный поиск по Wikipedia.
    # ------------------------------------------------------
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
        normalized_query = _normalize_place_name(query)

        if (
            not query
            or not normalized_query
            or normalized_query in checked_queries
        ):
            continue

        checked_queries.add(normalized_query)

        try:
            article_titles = _find_article_titles(query)

            for article_title in article_titles:
                article_data = _get_article_extract(article_title)

                if article_data:
                    article_data["query_used"] = query
                    article_data["match_type"] = "search"
                    return article_data

        except Exception:
            # Внешняя справка не должна мешать открытию маршрута.
            continue

    return None
