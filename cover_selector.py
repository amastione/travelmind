"""
Модуль выбора тематических изображений-обложек для TravelMind.

Логика:
- определяет сезон по дате начала путешествия;
- учитывает популярные туристические направления;
- учитывает тип поездки;
- выбирает файл из assets/covers;
- возвращает изображение в формате base64 data URL,
  пригодном для CSS background-image в Streamlit.
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

# Папка, где находится этот файл cover_selector.py.
PROJECT_ROOT = Path(__file__).resolve().parent

# Папка с изображениями-обложками.
COVERS_DIR = PROJECT_ROOT / "assets" / "covers"


# ==========================================================
# НАСТРОЙКИ СЕЗОНОВ
# ==========================================================

WINTER_MONTHS = {12, 1, 2}
SPRING_MONTHS = {3, 4, 5}
SUMMER_MONTHS = {6, 7, 8}
AUTUMN_MONTHS = {9, 10, 11}


# ==========================================================
# ПОПУЛЯРНЫЕ НАПРАВЛЕНИЯ
# Ключ — город / направление в нижнем регистре.
# Значение — тематическая группа.
# ==========================================================

DESTINATION_GROUPS = {
    # -------------------- Россия: северные города --------------------
    "сургут": "northern_city",
    "мурманск": "northern_city",
    "архангельск": "northern_city",
    "норильск": "northern_city",
    "якутск": "northern_city",
    "ханты-мансийск": "northern_city",
    "ханты мансийск": "northern_city",
    "новый уренгой": "northern_city",
    "салехард": "northern_city",

    # -------------------- Россия: Кавказ / горы --------------------
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

    # -------------------- Россия: море --------------------
    "сочи": "sea",
    "адлер": "sea",
    "анапа": "sea",
    "геленджик": "sea",
    "ялта": "sea",
    "севастополь": "sea",
    "крым": "sea",
    "краснодарский край": "sea",

    # -------------------- Россия: природа --------------------
    "байкал": "lake_nature",
    "иркутск": "lake_nature",
    "листвянка": "lake_nature",
    "карелия": "lake_nature",
    "петрозаводск": "lake_nature",
    "алтай": "lake_nature",
    "горный алтай": "lake_nature",
    "телецкое озеро": "lake_nature",

    # -------------------- Россия: исторические и городские --------------------
    "москва": "city",
    "санкт-петербург": "europe_city",
    "санкт петербург": "europe_city",
    "петербург": "europe_city",
    "спб": "europe_city",
    "казань": "europe_city",
    "калининград": "europe_city",
    "нижний новгород": "city",
    "екатеринбург": "city",
    "новосибирск": "city",
    "самара": "city",
    "владивосток": "city",

    # -------------------- Европа --------------------
    "париж": "europe_city",
    "франция": "europe_city",
    "рим": "europe_city",
    "италия": "europe_city",
    "милан": "europe_city",
    "флоренция": "europe_city",
    "венеция": "europe_city",
    "барселона": "europe_city",
    "мадрид": "europe_city",
    "испания": "europe_city",
    "прага": "europe_city",
    "чехия": "europe_city",
    "вена": "europe_city",
    "австрия": "europe_city",
    "берлин": "europe_city",
    "германия": "europe_city",
    "амстердам": "europe_city",
    "нидерланды": "europe_city",
    "будапешт": "europe_city",
    "венгрия": "europe_city",
    "лондон": "europe_city",
    "великобритания": "europe_city",

    # -------------------- Горнолыжные и горные курорты --------------------
    "альпы": "mountains",
    "швейцария": "mountains",
    "инсбрук": "mountains",
    "непал": "mountains",
    "гималаи": "mountains",
    "грузия": "mountains",
    "тбилиси": "mountains",

    # -------------------- Пляжные направления --------------------
    "анталья": "sea",
    "турция": "sea",
    "кемер": "sea",
    "бодрум": "sea",
    "алания": "sea",
    "греция": "sea",
    "кипр": "sea",
    "мальта": "sea",
    "майорка": "sea",
    "португалия": "sea",

    # -------------------- Тропики / острова --------------------
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

    # -------------------- Восток / пустыня --------------------
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

    # -------------------- Исторические восточные города --------------------
    "стамбул": "europe_city",
    "турция стамбул": "europe_city",
}


# ==========================================================
# НОРМАЛИЗАЦИЯ ДАННЫХ
# ==========================================================

def normalize_text(value: Any) -> str:
    """
    Преобразует значение в безопасный текст:
    - убирает лишние пробелы;
    - приводит к нижнему регистру;
    - заменяет ё на е.
    """
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
    Получает номер месяца из даты.

    Поддерживает:
    - datetime.date;
    - datetime.datetime;
    - строку ISO: 2026-10-28;
    - строку интерфейса: 28/10/2026;
    - строку: 28.10.2026.
    """
    if start_date is None:
        return None

    if isinstance(start_date, datetime):
        return start_date.month

    if isinstance(start_date, date):
        return start_date.month

    text_value = str(start_date).strip()

    date_formats = (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y/%m/%d",
    )

    for date_format in date_formats:
        try:
            return datetime.strptime(text_value, date_format).month
        except ValueError:
            continue

    return None


def get_season(start_date: Any) -> str:
    """
    Определяет сезон по дате начала поездки.
    Если дата неизвестна — возвращает summer как нейтральный вариант.
    """
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


# ==========================================================
# ВЫБОР КАТЕГОРИИ ПУТЕШЕСТВИЯ
# ==========================================================

def detect_destination_group(destination: Any) -> str | None:
    """
    Определяет тематическую группу по названию направления.

    Сначала ищет точное совпадение.
    Затем ищет ключевое слово внутри строки.

    Примеры:
    - «Домбай, Россия» → caucasus
    - «Санкт-Петербург» → europe_city
    - «Поездка в Сочи» → sea
    """
    destination_normalized = normalize_text(destination)

    if not destination_normalized:
        return None

    # Точное совпадение.
    if destination_normalized in DESTINATION_GROUPS:
        return DESTINATION_GROUPS[destination_normalized]

    # Поиск известного направления внутри полного текста.
    for place_name, destination_group in DESTINATION_GROUPS.items():
        if place_name in destination_normalized:
            return destination_group

    return None


def detect_group_from_travel_type(travel_type: Any) -> str | None:
    """
    Определяет тематическую группу по типу путешествия.

    Поддерживает русские и английские варианты типов.
    """
    travel_type_normalized = normalize_text(travel_type)

    if not travel_type_normalized:
        return None

    if any(word in travel_type_normalized for word in (
        "пляж", "море", "морск", "курорт", "beach", "sea",
    )):
        return "sea"

    if any(word in travel_type_normalized for word in (
        "гор", "активн", "треккинг", "лыжи", "ski", "mountain",
        "adventure",
    )):
        return "mountains"

    if any(word in travel_type_normalized for word in (
        "природ", "озер", "лес", "nature", "lake", "eco",
    )):
        return "lake_nature"

    if any(word in travel_type_normalized for word in (
        "истор", "культур", "музе", "culture", "history",
    )):
        return "europe_city"

    if any(word in travel_type_normalized for word in (
        "тропик", "остров", "island", "tropical",
    )):
        return "tropical_island"

    if any(word in travel_type_normalized for word in (
        "город", "city", "шопинг", "гастроном",
    )):
        return "city"

    return None


# ==========================================================
# ВЫБОР ИМЕНИ ФАЙЛА ОБЛОЖКИ
# ==========================================================

def select_cover_filename(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
) -> str:
    """
    Возвращает имя файла обложки, например:
    caucasus_winter.webp

    Приоритет:
    1. Известное направление.
    2. Тип путешествия.
    3. Универсальная городская обложка по сезону.
    """
    season = get_season(start_date)

    # Сначала выбираем группу по конкретному направлению.
    destination_group = detect_destination_group(destination)

    # Если город неизвестен, используем тип поездки.
    if destination_group is None:
        destination_group = detect_group_from_travel_type(travel_type)

    # -------- Северный город --------
    if destination_group == "northern_city":
        if season in {"winter", "spring"}:
            return "northern_city_winter.webp"
        return "northern_city_autumn.webp"

    # -------- Кавказ --------
    if destination_group == "caucasus":
        if season in {"winter", "spring"}:
            return "caucasus_winter.webp"
        return "caucasus_summer.webp"

    # -------- Универсальные горы --------
    if destination_group == "mountains":
        if season in {"winter", "spring"}:
            return "mountains_winter.webp"
        return "mountains_summer.webp"

    # -------- Море --------
    if destination_group == "sea":
        if season in {"summer", "spring"}:
            return "sea_summer.webp"
        return "sea_sunset.webp"

    # -------- Тропики --------
    if destination_group == "tropical_island":
        return "tropical_island.webp"

    # -------- Озёра, леса, природа --------
    if destination_group == "lake_nature":
        return "lake_nature.webp"

    # -------- Восточные города / пустыня --------
    if destination_group == "desert_city":
        return "desert_city.webp"

    # -------- Европа --------
    if destination_group == "europe_city":
        if season == "winter":
            return "europe_winter.webp"
        return "europe_city.webp"

    # -------- Универсальный город --------
    if season == "winter":
        return "city_winter.webp"

    if season == "autumn":
        return "city_autumn.webp"

    # Весна и лето используют летнюю универсальную городскую обложку.
    return "city_summer.webp"


def get_cover_path(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
) -> Path:
    """
    Возвращает полный путь к изображению-обложке на сервере.
    """
    filename = select_cover_filename(
        destination=destination,
        start_date=start_date,
        travel_type=travel_type,
    )

    return COVERS_DIR / filename


# ==========================================================
# ПОДГОТОВКА ИЗОБРАЖЕНИЯ ДЛЯ CSS
# ==========================================================

@lru_cache(maxsize=64)
def _file_to_data_url(filename: str) -> str | None:
    """
    Читает локальный .webp-файл и превращает его в data URL.

    Результат можно вставить в CSS:
    background-image: url("data:image/webp;base64,...");

    lru_cache нужен, чтобы файл не считывался заново
    при каждом перезапуске компонента Streamlit.
    """
    image_path = COVERS_DIR / filename

    if not image_path.exists() or not image_path.is_file():
        return None

    try:
        image_bytes = image_path.read_bytes()
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")

        suffix = image_path.suffix.lower()

        mime_types = {
            ".webp": "image/webp",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }

        mime_type = mime_types.get(suffix, "image/webp")

        return f"data:{mime_type};base64,{encoded_image}"

    except OSError:
        return None


def get_cover_data_url(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
) -> str | None:
    """
    Главная функция для страниц Streamlit.

    Возвращает:
    - data URL изображения, если файл найден;
    - None, если изображения нет.

    Пример:
    cover_url = get_cover_data_url("Домбай", "2027-02-14", "Активный отдых")
    """
    filename = select_cover_filename(
        destination=destination,
        start_date=start_date,
        travel_type=travel_type,
    )

    cover_data_url = _file_to_data_url(filename)

    # Если конкретной тематической обложки нет,
    # пробуем показать универсальную летнюю городскую обложку.
    if cover_data_url is None and filename != "city_summer.webp":
        cover_data_url = _file_to_data_url("city_summer.webp")

    return cover_data_url


def get_cover_metadata(
    destination: Any,
    start_date: Any = None,
    travel_type: Any = None,
) -> dict[str, str]:
    """
    Вспомогательная функция для отладки и будущих функций.

    Возвращает словарь:
    {
        "filename": "caucasus_winter.webp",
        "season": "winter",
        "group": "caucasus"
    }
    """
    return {
        "filename": select_cover_filename(
            destination=destination,
            start_date=start_date,
            travel_type=travel_type,
        ),
        "season": get_season(start_date),
        "group": (
            detect_destination_group(destination)
            or detect_group_from_travel_type(travel_type)
            or "city"
        ),
    }
