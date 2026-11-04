"""Тёмный autocomplete-компонент направления для TravelMind."""

from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT_DIR = (
    Path(__file__).parent / "destination_autocomplete_frontend"
)

_destination_autocomplete = components.declare_component(
    "destination_autocomplete",
    path=str(_COMPONENT_DIR),
)


def destination_autocomplete(
    *,
    value: str,
    suggestions: list[dict],
    hide_suggestions: bool,
    key: str,
):
    """
    Отображает единое поле направления с выпадающими подсказками.

    Возвращает:
    - {"type": "input", "value": "..."} — пользователь изменил текст;
    - {"type": "select", "value": "..."} — пользователь выбрал подсказку;
    - None — если действий не было.
    """
    return _destination_autocomplete(
        value=value or "",
        suggestions=suggestions or [],
        hide_suggestions=hide_suggestions,
        key=key,
        default=None,
    )
