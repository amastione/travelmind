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
