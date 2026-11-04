"""Компонент ввода направления TravelMind."""

from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT_DIR = (
    Path(__file__).resolve().parent
    / "destination_autocomplete_frontend"
)

_component = components.declare_component(
    "destination_autocomplete",
    path=str(_COMPONENT_DIR),
)


def destination_autocomplete(
    *,
    value,
    suggestions,
    hide_suggestions,
    key,
):
    return _component(
        value=value or "",
        suggestions=suggestions or [],
        hide_suggestions=bool(hide_suggestions),
        key=key,
        default=None,
    )
