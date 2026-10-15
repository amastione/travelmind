"""
Модуль выбора тематических обложек путешествий TravelMind.

Обложка определяется на основе:
- направления;
- месяца начала поездки;
- типа путешествия.

Все изображения должны лежать в:
assets/covers/
"""

from __future__ import annotations

import base64
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


# ==========================================================
# ПУТИ К ПАПКАМ ПРОЕКТА
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent
COVERS_DIR = PROJECT_ROOT / "assets" / "covers"


# ==========================================================
# СЕЗОНЫ
# ==========================================================

WINTER_MONTHS = {12, 1, 2}
SPRING_MONTHS = {3, 4, 5}
SUMMER_MONTHS = {6, 7, 8}
AUTUMN_MONTHS = {9, 10, 11}


# ==========================================================
# ИЗВЕСТНЫЕ НАПРАВЛЕНИЯ
# ==========================================================

DESTINATION_GROUPS = {
    # ------------------------------------------------------
    # Отдельные персональные обложки
    # ------------------------------------------------------
    "москва": "moscow",
    "moscow": "moscow",

    "санкт-петербург": "saint_peter",
    "санкт петербург": "saint_peter",
    "петербург": "saint_peter",
    "спб": "saint_peter",
    "saint petersburg": "saint_peter",
    "st petersburg": "saint_peter",

    "сочи": "sochi",
    "sochi": "sochi",

    # ------------------------------------------------------
    # Северные города
    # ------------------------------------------------------
    "сургут": "northern_city",
    "мурманск": "northern_city",
    "архангельск": "northern_city",
    "норильск": "northern_city",
    "якутск": "northern_city",
    "ханты-мансийск": "northern_city",
    "ханты мансийск": "northern_city",
    "новый уренгой": "northern_city",
    "салехард": "northern_city",

    # ------------------------------------------------------
    # Кавказ
    # ------------------------------------------------------
    "домбай": "caucasus",
    "архыз": "caucasus",
    "эльбрус": "caucasus",
    "приэльбрусье": "caucasus",
    "кисловодск": "caucasus",
    "пятигорск": "caucasus",
    "есентуки": "caucasus",
    "минеральные воды": "caucasus",
    "кавказ": "caucasus",
    "северный кавказ": "caucasus",

    # ------------------------------------------------------
    # Прочие горные направления
    # ------------------------------------------------------
    "алтай": "mountains",
    "горный алтай": "mountains",
    "грузия": "mountains",
    "тбилиси": "mountains",
    "альпы": "mountains",
    "швейцария": "mountains",
    "инсбрук": "mountains",
    "непал": "mountains",
    "гималаи": "mountains",

    # ------------------------------------------------------
    # Море и пляж
    # ------------------------------------------------------
    "адлер": "sea",
    "анапа": "sea",
    "геленджик": "sea",
    "ялта": "sea",
    "севастополь": "sea",
    "крым": "sea",
    "анталья": "sea",
    "кемер": "sea",
    "алания": "sea",
    "бодрум": "sea",
    "турция": "sea",
    "греция": "sea",
    "кипр": "sea",
    "мальта": "sea",
    "майорка": "sea",
    "португалия": "sea",

    # ------------------------------------------------------
    # Европейские города
    # ------------------------------------------------------
    "казань": "europe_city",
    "калининград": "europe_city",
    "париж": "europe_city",
    "рим": "europe_city",
    "милан": "europe_city",
    "флоренция": "europe_city",
    "венеция": "europe_city",
    "барселона": "europe_city",
    "мадрид": "europe_city",
    "прага": "europe_city",
    "вена": "europe_city",
    "берлин": "europe_city",
    "амстердам": "europe_city",
    "будапешт": "europe_city",
    "лондон": "europe_city",
    "стамбул": "europe_city",
    "италия": "europe_city",
    "франция": "europe_city",
    "испания": "europe_city",
    "чехия": "europe_city",
    "австрия": "europe_city",
    "германия": "europe_city",
    "нидерланды": "europe_city",
    "венгрия": "europe_city",
    "великобритания": "europe_city",

    # ------------------------------------------------------
    # Тропики и острова
    # ------------------------------------------------------
    "бали": "tropical_island",
    "индонезия": "tropical_island",
    "пхукет": "tropical_island",
    "таиланд": "tropical_island",
    "самуи": "tropical_island",
    "мальдивы": "tropical_island",
    "сейшелы": "tropical_island",
    "шри-ланка": "tropical_island",
    "шри ланка": "tropical_island",
    "гоа": "tropical_island",

    # ------------------------------------------------------
    # Восток / пустыня
    # ------------------------------------------------------
    "дубай": "desert_city",
    "абу-даби": "desert_city",
    "абу даби": "desert_city",
    "оаэ": "desert_city",
    "эмираты": "desert_city",
    "египет": "desert_city",
    "каир": "desert_city",
    "марракеш": "desert_city",
    "марокко": "desert_city",
    "иордания": "desert_city",
    "доха": "desert_city",
}


def normalize_text(value: Any) -> str:
    """Нормализует текст для безопасного поиска."""
    if value is None:
        return ""

    return " ".join(
        str(value)
        .strip()
        .lower()
        .replace("ё", "е")
        .split()
    )


def extract_month(start_date: Any) -> int | None:
    """Получает месяц из date/datetime или из распространённых строковых форматов."""
    if start_date is None:
        return None

    if isinstance(start_date, datetime):
        return start_date.month

    if isinstance(start_date, date):
        return start_date.month

    text_value = str(start_date).strip()

    for date_format in (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y/%m/%d",
    ):
        try:
            return datetime.strptime(text_value, date_format).month
        except ValueError:
            continue

    return None


def get_season(start_date: Any) -> str:
    """Возвращает winter, spring, summer или autumn."""
    month = extract_month(start_date)

    if month in WINTER_MONTHS:
        return "winter"

    if month in SPRING_MONTHS:
        return "spring"

    if month in SUMMER_MONTHS:
        return "summer"

    if month in AUTUMN_MONTHS:
        return "autumn"

    return "summer"


def detect_destination_group(destination: Any) -> str | None:
    """
    Определяет группу направления.

    Поддерживает, например:
    «Домбай, Россия» → caucasus
    «Путешествие в Сочи» → sochi
    """
    normalized_destination = normalize_text(destination)

    if not normalized_destination:
        return None

    if normalized_destination in DESTINATION_GROUPS:
        return DESTINATION_GROUPS[normalized_destination]

    # Сначала ищем длинные названия, затем короткие.
    # Так «санкт-петербург» будет обработан корректно.
    sorted_places = sorted(
        DESTINATION_GROUPS.items(),
        key=lambda item: len(item[0]),
        reverse=True,
    )

    for place_name, group_name in sorted_places:
        if place_name in normalized_destination:
            return group_name

    return None


def detect_group_from_travel_type(travel_type: Any) -> str | None:
    """Определяет тему, если конкретное направление неизвестно."""
    normalized_type = normalize_text(travel_type)

    if not normalized_type:
        return None

    if any(word in normalized_type for word in (
        "пляж", "море", "морск", "курорт", "beach", "sea",
    )):
        return "sea"

    if any(word in normalized_type for word in (
        "гор", "активн", "треккинг", "лыжи", "ski", "mountain",
        "adventure",
    )):
        return "mountains"

    if any(word in normalized_type for word in (
        "тропик", "остров", "island", "tropical",
    )):
        return "tropical_island"

    if any(word in normalized_type for word in (
        "истор", "культур", "музе", "culture", "history",
    )):
        return "europe_city"

    if any(word in normalized_type for word in (
        "город", "city", "гастроном", "шопинг",
    )):
        return "city"

    return None


def select_cover_filename(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
) -> str:
    """
    Выбирает точное имя файла из assets/covers.

    Важно: все названия в этой функции совпадают с именами
    файлов, показанных на вашем скриншоте.
    """
    season = get_season(start_date)

    group_name = (
        detect_destination_group(destination)
        or detect_group_from_travel_type(travel_type)
        or "city"
    )

    # Индивидуальная обложка Москвы.
    if group_name == "moscow":
        return "moscow_summer.webp"

    # Индивидуальная обложка Санкт-Петербурга.
    if group_name == "saint_peter":
        return "saint_peter.webp"

    # Индивидуальная обложка Сочи.
    if group_name == "sochi":
        return "sochi.webp"

    # Северные города: зимой — снег, в остальные сезоны — северная осень.
    if group_name == "northern_city":
        if season in {"winter", "spring"}:
            return "northern_city_winter.webp"
        return "northern_city_autumn.webp"

    # Кавказ.
    if group_name == "caucasus":
        if season in {"winter", "spring"}:
            return "caucasus_winter.webp"
        return "caucasus_summer.webp"

    # Универсальные горы.
    if group_name == "mountains":
        if season in {"winter", "spring"}:
            return "mountains_winter.webp"
        return "mountains_summer.webp"

    # Море: летом и весной — дневной пляж, осенью и зимой — закат.
    if group_name == "sea":
        if season in {"spring", "summer"}:
            return "sea_summer.webp"
        return "sea_sunset.webp"

    # Тропические направления.
    if group_name == "tropical_island":
        return "tropical_island.webp"

    # Города Востока и пустыня.
    if group_name == "desert_city":
        return "desert_city.webp"

    # Европейские города.
    if group_name == "europe_city":
        if season == "winter":
            return "europe_winter.webp"
        return "europe_city.webp"

    # Универсальные городские фоны.
    if season == "winter":
        return "city_winter.webp"

    if season == "autumn":
        return "city_autumn.webp"

    return "city_summer.webp"


@lru_cache(maxsize=64)
def _file_to_data_url(filename: str) -> str | None:
    """
    Читает файл из assets/covers и превращает его в data URL.
    Data URL можно безопасно использовать в CSS background-image.
    """
    image_path = COVERS_DIR / filename

    if not image_path.exists() or not image_path.is_file():
        return None

    try:
        image_bytes = image_path.read_bytes()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    except OSError:
        return None

    suffix = image_path.suffix.lower()

    mime_type = {
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(suffix, "image/webp")

    return f"data:{mime_type};base64,{encoded_image}"


def get_cover_data_url(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
) -> str | None:
    """
    Основная функция для страниц.

    Возвращает data URL подходящей картинки или None,
    если файл не удалось найти.
    """
    filename = select_cover_filename(
        destination=destination,
        start_date=start_date,
        travel_type=travel_type,
    )

    cover_data_url = _file_to_data_url(filename)

    # Безопасный запасной фон, если конкретное изображение отсутствует.
    if cover_data_url is None and filename != "city_summer.webp":
        cover_data_url = _file_to_data_url("city_summer.webp")

    return cover_data_url


def get_cover_metadata(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
) -> dict[str, str]:
    """Возвращает служебную информацию для проверки и отладки."""
    group_name = (
        detect_destination_group(destination)
        or detect_group_from_travel_type(travel_type)
        or "city"
    )

    return {
        "filename": select_cover_filename(
            destination=destination,
            start_date=start_date,
            travel_type=travel_type,
        ),
        "season": get_season(start_date),
        "group": group_name,
    }
