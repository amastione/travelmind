"""
Выбор тематических изображений-обложек для TravelMind.

Приоритет выбора:
1. cover_profile, возвращённый AI при генерации маршрута.
2. Резервная классификация по названию направления, дате и типу поездки.
3. Универсальная городская обложка.

Изображения должны находиться в:
assets/covers/
"""

from __future__ import annotations

import base64
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any


# ==========================================================
# ПУТИ К ФАЙЛАМ
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent
COVERS_DIR = PROJECT_ROOT / "assets" / "covers"


# ==========================================================
# ПРОФИЛИ, КОТОРЫЕ МОЖЕТ ВЕРНУТЬ AI
# ==========================================================
#
# Ключ — cover_profile из JSON маршрута.
# Значение — реально существующий файл в assets/covers/.
# ==========================================================

COVER_PROFILE_FILES = {
    "city_summer": "city_summer.webp",
    "city_autumn": "city_autumn.webp",
    "city_winter": "city_winter.webp",
    "moscow": "moscow_summer.webp",
    "saint_peter": "saint_peter.webp",
    "sochi": "sochi.webp",
    "northern_city_autumn": "northern_city_autumn.webp",
    "northern_city_winter": "northern_city_winter.webp",
    "caucasus_summer": "caucasus_summer.webp",
    "caucasus_winter": "caucasus_winter.webp",
    "mountains_summer": "mountains_summer.webp",
    "mountains_winter": "mountains_winter.webp",
    "sea_summer": "sea_summer.webp",
    "sea_sunset": "sea_sunset.webp",
    "europe_city": "europe_city.webp",
    "europe_winter": "europe_winter.webp",
    "tropical_island": "tropical_island.webp",
    "desert_city": "desert_city.webp",
}


# ==========================================================
# СЕЗОНЫ
# ==========================================================

WINTER_MONTHS = {12, 1, 2}
SPRING_MONTHS = {3, 4, 5}
SUMMER_MONTHS = {6, 7, 8}
AUTUMN_MONTHS = {9, 10, 11}


# ==========================================================
# FALLBACK-КЛАССИФИКАЦИЯ СТАРЫХ МАРШРУТОВ
# ==========================================================
#
# Нужна только для поездок, созданных до cover_profile.
# Для новых маршрутов решение принимает AI.
# ==========================================================

DESTINATION_GROUPS = {
    # Москва и Московская агломерация
    "москва": "moscow",
    "moscow": "moscow",
    "переделкино": "moscow",
    "зеленоград": "moscow",
    "химки": "moscow",
    "мытищи": "moscow",
    "одинцово": "moscow",
    "красногорск": "moscow",
    "балашиха": "moscow",

    # Санкт-Петербург и пригороды
    "санкт-петербург": "saint_peter",
    "санкт петербург": "saint_peter",
    "петербург": "saint_peter",
    "спб": "saint_peter",
    "saint petersburg": "saint_peter",
    "st petersburg": "saint_peter",
    "петергоф": "saint_peter",
    "пушкин": "saint_peter",
    "павловск": "saint_peter",
    "кронштадт": "saint_peter",
    "стрельна": "saint_peter",

    # Сочи и близкие курорты
    "сочи": "sochi",
    "sochi": "sochi",
    "адлер": "sochi",
    "красная поляна": "sochi",
    "роза хутор": "sochi",

    # Северные города
    "сургут": "northern_city",
    "мурманск": "northern_city",
    "архангельск": "northern_city",
    "норильск": "northern_city",
    "якутск": "northern_city",
    "ханты-мансийск": "northern_city",
    "ханты мансийск": "northern_city",
    "новый уренгой": "northern_city",
    "салехард": "northern_city",

    # Кавказ
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

    # Другие горные направления
    "алтай": "mountains",
    "горный алтай": "mountains",
    "грузия": "mountains",
    "тбилиси": "mountains",
    "альпы": "mountains",
    "швейцария": "mountains",
    "инсбрук": "mountains",
    "непал": "mountains",
    "гималаи": "mountains",

    # Море / пляж
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

    # Европейские города
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

    # Тропики
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

    # Восток / пустыня
    "дубай": "desert_city",
    "абу-даби": "desert_city",
    "абу даби": "desert_city",
    "оаэ": "desert_city",
    "эмираты": "desert_city",
    "египет": "desert_city",
    "каир": "desert_city",
    "марракеш": "desert_city",
    "марокко": "desert_city",
    "доха": "desert_city",
}


# ==========================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================================

def normalize_text(value: Any) -> str:
    """Приводит текст к удобному для сравнения виду."""
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
    """
    Получает месяц из даты.

    Поддерживаются date, datetime и строки:
    YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY.
    """
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
    """Возвращает сезон: winter, spring, summer или autumn."""
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
    """Определяет группу направления для старых маршрутов."""
    normalized_destination = normalize_text(destination)

    if not normalized_destination:
        return None

    if normalized_destination in DESTINATION_GROUPS:
        return DESTINATION_GROUPS[normalized_destination]

    # Длинные названия проверяем раньше коротких.
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
    """Определяет группу по типу путешествия, если город неизвестен."""
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

    return None


# ==========================================================
# ВЫБОР ПРОФИЛЯ И ИМЕНИ ФАЙЛА
# ==========================================================

def normalize_cover_profile(cover_profile: Any) -> str:
    """
    Проверяет profile от AI.

    Возвращает пустую строку, если профиль отсутствует
    или его нет среди разрешённых.
    """
    profile = normalize_text(cover_profile)

    return profile if profile in COVER_PROFILE_FILES else ""


def select_fallback_profile(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
) -> str:
    """
    Резервный выбор профиля для старых маршрутов,
    в которых нет cover_profile от AI.
    """
    season = get_season(start_date)

    group_name = (
        detect_destination_group(destination)
        or detect_group_from_travel_type(travel_type)
        or "city"
    )

    if group_name in {"moscow", "saint_peter", "sochi"}:
        return group_name

    if group_name == "northern_city":
        if season in {"winter", "spring"}:
            return "northern_city_winter"
        return "northern_city_autumn"

    if group_name == "caucasus":
        if season in {"winter", "spring"}:
            return "caucasus_winter"
        return "caucasus_summer"

    if group_name == "mountains":
        if season in {"winter", "spring"}:
            return "mountains_winter"
        return "mountains_summer"

    if group_name == "sea":
        if season in {"spring", "summer"}:
            return "sea_summer"
        return "sea_sunset"

    if group_name == "tropical_island":
        return "tropical_island"

    if group_name == "desert_city":
        return "desert_city"

    if group_name == "europe_city":
        if season == "winter":
            return "europe_winter"
        return "europe_city"

    if season == "winter":
        return "city_winter"

    if season == "autumn":
        return "city_autumn"

    return "city_summer"


def select_cover_profile(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
    cover_profile: Any = None,
) -> str:
    """
    Возвращает итоговый профиль.

    Если у новой поездки есть корректный AI-профиль — берём его.
    Если нет — используем fallback-правила.
    """
    ai_profile = normalize_cover_profile(cover_profile)

    if ai_profile:
        return ai_profile

    return select_fallback_profile(
        destination=destination,
        start_date=start_date,
        travel_type=travel_type,
    )


def select_cover_filename(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
    cover_profile: Any = None,
) -> str:
    """Возвращает имя файла картинки для выбранного профиля."""
    profile = select_cover_profile(
        destination=destination,
        start_date=start_date,
        travel_type=travel_type,
        cover_profile=cover_profile,
    )

    return COVER_PROFILE_FILES.get(profile, "city_summer.webp")


# ==========================================================
# ПРЕОБРАЗОВАНИЕ КАРТИНКИ В CSS DATA URL
# ==========================================================

@lru_cache(maxsize=64)
def _file_to_data_url(filename: str) -> str | None:
    """
    Считывает картинку и возвращает data URL.

    Такой URL можно вставить в:
    background-image: url('data:image/webp;base64,...');
    """
    image_path = COVERS_DIR / filename

    if not image_path.exists() or not image_path.is_file():
        return None

    try:
        image_bytes = image_path.read_bytes()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
    except OSError:
        return None

    mime_type = {
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(image_path.suffix.lower(), "image/webp")

    return f"data:{mime_type};base64,{encoded_image}"


def get_cover_data_url(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
    cover_profile: Any = None,
) -> str | None:
    """
    Главная функция для Streamlit-страниц.

    Новые поездки:
        cover_profile от AI → картинка.

    Старые поездки:
        направление + дата + тип → fallback-картинка.
    """
    filename = select_cover_filename(
        destination=destination,
        start_date=start_date,
        travel_type=travel_type,
        cover_profile=cover_profile,
    )

    image_url = _file_to_data_url(filename)

    # Последняя страховка: универсальный летний городской фон.
    if image_url is None and filename != "city_summer.webp":
        image_url = _file_to_data_url("city_summer.webp")

    return image_url


def get_cover_metadata(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
    cover_profile: Any = None,
) -> dict[str, str]:
    """
    Служебная функция для отладки.

    Можно использовать, чтобы проверить выбор:
    {
      "profile": "moscow",
      "filename": "moscow_summer.webp",
      "season": "autumn",
      "source": "ai"
    }
    """
    valid_ai_profile = normalize_cover_profile(cover_profile)

    profile = select_cover_profile(
        destination=destination,
        start_date=start_date,
        travel_type=travel_type,
        cover_profile=cover_profile,
    )

    return {
        "profile": profile,
        "filename": COVER_PROFILE_FILES.get(
            profile,
            "city_summer.webp",
        ),
        "season": get_season(start_date),
        "source": "ai" if valid_ai_profile else "fallback",
    }
