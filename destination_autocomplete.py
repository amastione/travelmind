"""Компонент ввода направления TravelMind."""

from pathlib import Path

import streamlit.components.v1 as components


_COMPONENT_DIR = (
    Path(__file__).resolve().parent
    / "destination_autocomplete_frontend"
)

_INDEX_FILE = _COMPONENT_DIR / "index.html"

if not _INDEX_FILE.is_file():
    raise FileNotFoundError(
        f"Не найден HTML-файл компонента: {_INDEX_FILE}"
    )

print(
    "[destination_autocomplete] "
    f"HTML найден: {_INDEX_FILE}; "
    f"размер: {_INDEX_FILE.stat().st_size} байт",
    flush=True,
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
