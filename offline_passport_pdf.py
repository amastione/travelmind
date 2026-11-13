"""Генерация офлайн-паспорта поездки TravelMind в PDF."""

from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any
from html import escape, unescape
import re

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PAGE_BACKGROUND = colors.HexColor("#F7FAFC")
DARK_BLUE = colors.HexColor("#102A43")
TEXT_COLOR = colors.HexColor("#243B53")
MUTED_COLOR = colors.HexColor("#627D98")
CYAN = colors.HexColor("#0E7490")
LIGHT_CYAN = colors.HexColor("#E6F6F8")
LIGHT_BLUE = colors.HexColor("#EEF4F8")
BORDER_COLOR = colors.HexColor("#CBD5E1")
WARNING_BG = colors.HexColor("#FFF8DB")
WARNING_TEXT = colors.HexColor("#7C5A00")
SUCCESS_COLOR = colors.HexColor("#166534")


def _value(source: Any, key: str, default: Any = "") -> Any:
    """Безопасно получает значение как из dict, так и из sqlite.Row."""
    if source is None:
        return default

    try:
        value = source[key]
    except (KeyError, IndexError, TypeError):
        return default

    return default if value is None else value


def _text(value: Any, default: str = "—") -> str:
    """Подготавливает значение для вывода в PDF."""
    result = str(value or "").strip()
    return result if result else default


def _money(value: Any) -> float:
    """Безопасно преобразует стоимость в число."""
    try:
        return max(float(value or 0), 0)
    except (TypeError, ValueError):
        return 0.0


def _format_money(value: Any, currency: str) -> str:
    """Форматирует денежное значение."""
    amount = _money(value)

    if amount.is_integer():
        number = f"{int(amount):,}".replace(",", " ")
    else:
        number = f"{amount:,.2f}".replace(",", " ").replace(".", ",")

    return f"{number} {currency}"


def _register_cyrillic_font() -> tuple[str, str]:
    """
    Подключает DejaVu Sans с поддержкой кириллицы.

    Шрифты должны находиться в assets/fonts/ либо быть доступны
    в системных путях сервера.
    """
    regular_paths = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
        Path("assets/fonts/DejaVuSans.ttf"),
    ]

    bold_paths = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
        Path("assets/fonts/DejaVuSans-Bold.ttf"),
    ]

    regular_path = next(
        (path for path in regular_paths if path.exists()),
        None,
    )
    bold_path = next(
        (path for path in bold_paths if path.exists()),
        None,
    )

    if not regular_path or not bold_path:
        raise RuntimeError(
            "Не найден шрифт для русского текста в PDF. "
            "Добавьте DejaVuSans.ttf и DejaVuSans-Bold.ttf "
            "в папку assets/fonts/."
        )

    regular_name = "TravelMindDejaVu"
    bold_name = "TravelMindDejaVuBold"

    registered = pdfmetrics.getRegisteredFontNames()

    if regular_name not in registered:
        pdfmetrics.registerFont(
            TTFont(regular_name, str(regular_path))
        )

    if bold_name not in registered:
        pdfmetrics.registerFont(
            TTFont(bold_name, str(bold_path))
        )
    pdfmetrics.registerFontFamily(
        regular_name,
        normal=regular_name,
        bold=bold_name,
        italic=regular_name,
        boldItalic=bold_name,
    )

    return regular_name, bold_name


def _paragraph(
    text: Any,
    style: ParagraphStyle,
) -> Paragraph:
    """
    Безопасно готовит текст для ReportLab.

    Поддерживаются только:
    - <b>текст</b> для жирного начертания;
    - <br>, <br/>, <br /> для переноса строки.

    Остальные HTML-теги не выводятся в PDF.
    """
    raw_text = _text(text, "")

    # Иногда в сохранённых данных теги могут быть экранированы:
    # &lt;br&gt; или даже &amp;lt;br&amp;gt;.
    # Двух проходов достаточно для ранее сформированных данных.
    raw_text = unescape(unescape(raw_text))

    # Заменяем допустимые теги временными маркерами.
    raw_text = re.sub(
        r"<\s*br\s*/?\s*>",
        "__TM_LINE_BREAK__",
        raw_text,
        flags=re.IGNORECASE,
    )
    raw_text = re.sub(
        r"<\s*b\s*>",
        "__TM_BOLD_OPEN__",
        raw_text,
        flags=re.IGNORECASE,
    )
    raw_text = re.sub(
        r"<\s*/\s*b\s*>",
        "__TM_BOLD_CLOSE__",
        raw_text,
        flags=re.IGNORECASE,
    )

    # Удаляем любые прочие HTML-подобные теги из старых данных.
    raw_text = re.sub(r"</?[^>]+>", "", raw_text)

    # Экранируем обычный текст, чтобы ReportLab не интерпретировал
    # случайные символы как собственную разметку.
    safe_text = escape(raw_text, quote=False)

    # Возвращаем только разрешённую разметку ReportLab.
    safe_text = safe_text.replace(
        "__TM_LINE_BREAK__",
        "<br/>",
    )
    safe_text = safe_text.replace(
        "__TM_BOLD_OPEN__",
        "<b>",
    )
    safe_text = safe_text.replace(
        "__TM_BOLD_CLOSE__",
        "</b>",
    )
    safe_text = safe_text.replace("\n", "<br/>")

    return Paragraph(safe_text, style)


def _section_title(
    title: str,
    styles: dict[str, ParagraphStyle],
) -> list:
    """Возвращает заголовок секции с отступом."""
    return [
        Spacer(1, 0.35 * cm),
        Paragraph(title, styles["section"]),
        Spacer(1, 0.14 * cm),
    ]


def _footer(canvas, document) -> None:
    """Рисует номер страницы."""
    canvas.saveState()

    canvas.setStrokeColor(BORDER_COLOR)
    canvas.setLineWidth(0.4)
    canvas.line(
        document.leftMargin,
        1.25 * cm,
        A4[0] - document.rightMargin,
        1.25 * cm,
    )

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED_COLOR)
    canvas.drawString(
        document.leftMargin,
        0.82 * cm,
        "TravelMind · Офлайн-паспорт поездки",
    )

    canvas.drawRightString(
        A4[0] - document.rightMargin,
        0.82 * cm,
        f"Страница {document.page}",
    )

    canvas.restoreState()


def build_offline_passport_pdf(
    trip: Any,
    data: dict,
    expenses: list[Any],
    checklist_sections: list[tuple[str, list[str]]],
    checklist_statuses: dict[str, bool],
    checklist_key_builder,
) -> bytes:
    """
    Собирает офлайн-паспорт поездки в PDF и возвращает его как bytes.

    AI-запросы не выполняются: используются только данные сохранённой поездки.
    """
    regular_font, bold_font = _register_cyrillic_font()

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=1.45 * cm,
        rightMargin=1.45 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.65 * cm,
        title="TravelMind — офлайн-паспорт поездки",
        author="TravelMind",
    )

    base_styles = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "TravelMindTitle",
            parent=base_styles["Title"],
            fontName=bold_font,
            fontSize=25,
            leading=30,
            textColor=DARK_BLUE,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "TravelMindSubtitle",
            parent=base_styles["Normal"],
            fontName=regular_font,
            fontSize=11,
            leading=16,
            textColor=MUTED_COLOR,
            alignment=TA_CENTER,
            spaceAfter=14,
        ),
        "section": ParagraphStyle(
            "TravelMindSection",
            parent=base_styles["Heading2"],
            fontName=bold_font,
            fontSize=15,
            leading=20,
            textColor=DARK_BLUE,
            spaceBefore=4,
            spaceAfter=4,
        ),
        "day": ParagraphStyle(
            "TravelMindDay",
            parent=base_styles["Heading3"],
            fontName=bold_font,
            fontSize=12,
            leading=16,
            textColor=CYAN,
            spaceAfter=5,
        ),
        "normal": ParagraphStyle(
            "TravelMindNormal",
            parent=base_styles["Normal"],
            fontName=regular_font,
            fontSize=9.5,
            leading=14,
            textColor=TEXT_COLOR,
            alignment=TA_LEFT,
        ),
        "small": ParagraphStyle(
            "TravelMindSmall",
            parent=base_styles["Normal"],
            fontName=regular_font,
            fontSize=8.3,
            leading=11.5,
            textColor=MUTED_COLOR,
        ),
        "table_head": ParagraphStyle(
            "TravelMindTableHead",
            parent=base_styles["Normal"],
            fontName=bold_font,
            fontSize=8.3,
            leading=10,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "TravelMindTableCell",
            parent=base_styles["Normal"],
            fontName=regular_font,
            fontSize=8.2,
            leading=11,
            textColor=TEXT_COLOR,
        ),
        "table_cell_bold": ParagraphStyle(
            "TravelMindTableCellBold",
            parent=base_styles["Normal"],
            fontName=bold_font,
            fontSize=8.2,
            leading=11,
            textColor=TEXT_COLOR,
        ),
        "warning": ParagraphStyle(
            "TravelMindWarning",
            parent=base_styles["Normal"],
            fontName=regular_font,
            fontSize=8.8,
            leading=13,
            textColor=WARNING_TEXT,
        ),
    }

    currency = _text(_value(trip, "currency", "RUB"), "RUB")
    trip_id = _value(trip, "id", 0)

    destination = _text(
        data.get("destination")
        or _value(trip, "destination")
        or data.get("city"),
        "Направление не указано",
    )

    title = _text(
        data.get("title")
        or data.get("trip_title")
        or _value(trip, "title"),
        destination,
    )

    start_date = _text(
        data.get("start_date") or _value(trip, "start_date"),
        "дата не указана",
    )
    end_date = _text(
        data.get("end_date") or _value(trip, "end_date"),
        "дата не указана",
    )

    people = (
        data.get("people")
        or data.get("people_count")
        or _value(trip, "people_count", 1)
    )

    total_budget = (
        data.get("budget")
        or data.get("total_budget")
        or _value(trip, "budget", 0)
    )

    days = data.get("days") or []
    hotels = data.get("hotels") or []
    accommodation = data.get("accommodation") or {}

    story = []

    # ==========================================================
    # 1. ОБЛОЖКА
    # ==========================================================
    story.extend(
        [
            Spacer(1, 0.7 * cm),
            Paragraph("TravelMind", styles["title"]),
            Paragraph("Офлайн-паспорт поездки", styles["subtitle"]),
        ]
    )

    cover_rows = [
        [
            _paragraph("<b>Поездка</b>", styles["table_cell_bold"]),
            _paragraph(title, styles["table_cell"]),
        ],
        [
            _paragraph("<b>Направление</b>", styles["table_cell_bold"]),
            _paragraph(destination, styles["table_cell"]),
        ],
        [
            _paragraph("<b>Даты</b>", styles["table_cell_bold"]),
            _paragraph(f"{start_date} — {end_date}", styles["table_cell"]),
        ],
        [
            _paragraph("<b>Путешественники</b>", styles["table_cell_bold"]),
            _paragraph(str(people), styles["table_cell"]),
        ],
        [
            _paragraph("<b>Плановый бюджет</b>", styles["table_cell_bold"]),
            _paragraph(
                _format_money(total_budget, currency),
                styles["table_cell"],
            ),
        ],
        [
            _paragraph("<b>Сформировано</b>", styles["table_cell_bold"]),
            _paragraph(
                date.today().strftime("%d.%m.%Y"),
                styles["table_cell"],
            ),
        ],
    ]

    cover_table = Table(
        cover_rows,
        colWidths=[4.3 * cm, 12.2 * cm],
    )
    cover_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT_CYAN),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(cover_table)
    story.append(Spacer(1, 0.35 * cm))

    warning_table = Table(
        [[
            _paragraph(
                "⚠️ Этот документ предназначен для использования "
                "без интернета. Перед выездом проверьте официальные "
                "расписания, цены, бронирования, погоду, дорожную "
                "обстановку и требования к посещению мест.",
                styles["warning"],
            )
        ]],
        colWidths=[16.5 * cm],
    )
    warning_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), WARNING_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#F5D76E")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]
        )
    )
    story.append(warning_table)

    # ==========================================================
    # 2. БЫСТРЫЙ ПЛАН
    # ==========================================================
    story.extend(_section_title("1. Быстрый план поездки", styles))

    quick_plan = [[
        _paragraph("День", styles["table_head"]),
        _paragraph("Дата", styles["table_head"]),
        _paragraph("Главное на день", styles["table_head"]),
    ]]

    for index, day_data in enumerate(days, start=1):
        if not isinstance(day_data, dict):
            continue

        activities = day_data.get("activities") or []
        first_titles = []

        for activity in activities[:3]:
            if isinstance(activity, dict):
                activity_title = _text(activity.get("title"), "")
                if activity_title:
                    first_titles.append(activity_title)

        overview = _text(day_data.get("overview"), "")
        main_plan = " · ".join(first_titles) or overview or "План уточняется"

        quick_plan.append(
            [
                _paragraph(f"День {index}", styles["table_cell_bold"]),
                _paragraph(
                    _text(day_data.get("date")),
                    styles["table_cell"],
                ),
                _paragraph(main_plan, styles["table_cell"]),
            ]
        )

    if len(quick_plan) == 1:
        quick_plan.append(
            [
                _paragraph("—", styles["table_cell"]),
                _paragraph("—", styles["table_cell"]),
                _paragraph(
                    "Маршрут по дням пока не сформирован.",
                    styles["table_cell"],
                ),
            ]
        )

    quick_table = Table(
        quick_plan,
        colWidths=[2.3 * cm, 3.1 * cm, 11.1 * cm],
        repeatRows=1,
    )
    quick_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(quick_table)

    # ==========================================================
    # 3. ПОДРОБНЫЙ МАРШРУТ
    # ==========================================================
    story.extend(_section_title("2. Подробный маршрут", styles))

    if not days:
        story.append(
            _paragraph(
                "В сохранённой поездке пока нет маршрута по дням.",
                styles["normal"],
            )
        )

    for day_number, day_data in enumerate(days, start=1):
        if not isinstance(day_data, dict):
            continue

        day_date = _text(day_data.get("date"), "")
        overview = _text(day_data.get("overview"), "")

        story.append(
            Paragraph(
                f"День {day_number}"
                + (f" · {day_date}" if day_date else ""),
                styles["day"],
            )
        )

        if overview:
            story.append(_paragraph(overview, styles["normal"]))
            story.append(Spacer(1, 0.1 * cm))

        activities = day_data.get("activities") or []

        if not activities:
            story.append(
                _paragraph(
                    "Активности на этот день не указаны.",
                    styles["small"],
                )
            )
            continue

        for activity_index, activity in enumerate(activities, start=1):
            if not isinstance(activity, dict):
                continue

            activity_title = _text(
                activity.get("title"),
                "Активность без названия",
            )
            activity_time = _text(activity.get("time"), "")
            activity_location = _text(activity.get("location"), "")
            activity_description = _text(activity.get("description"), "")
            activity_tip = _text(activity.get("tip"), "")
            activity_cost = _money(activity.get("cost"))

            coordinates = ""

            lat = activity.get("lat")
            lon = activity.get("lon")

            if lat not in (None, "") and lon not in (None, ""):
                coordinates = f"{lat}, {lon}"

            activity_lines = []

            header = (
                f"<b>{activity_index}. {activity_title}</b>"
                + (f" · {activity_time}" if activity_time else "")
            )
            activity_lines.append(header)

            if activity_location:
                activity_lines.append(
                    f"<b>Место:</b> {activity_location}"
                )

            if coordinates:
                activity_lines.append(
                    f"<b>Координаты:</b> {coordinates}"
                )

            if activity_cost > 0:
                activity_lines.append(
                    f"<b>Ориентировочная стоимость:</b> "
                    f"{_format_money(activity_cost, currency)}"
                )

            if activity_description:
                activity_lines.append(activity_description)

            if activity_tip:
                activity_lines.append(
                    f"<b>Важно:</b> {activity_tip}"
                )

            activity_table = Table(
                [[_paragraph("<br/>".join(activity_lines), styles["normal"])]],
                colWidths=[16.5 * cm],
            )
            activity_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
                        ("BOX", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
                        ("LEFTPADDING", (0, 0), (-1, -1), 9),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                        ("TOPPADDING", (0, 0), (-1, -1), 7),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ]
                )
            )

            story.append(KeepTogether(activity_table))
            story.append(Spacer(1, 0.11 * cm))

    # ==========================================================
    # 4. ПРОЖИВАНИЕ
    # ==========================================================
    story.extend(_section_title("3. Проживание и бронирования", styles))

    accommodation_items = []

    if isinstance(accommodation, dict) and accommodation:
        accommodation_items.append(accommodation)

    if isinstance(hotels, list):
        accommodation_items.extend(
            hotel for hotel in hotels if isinstance(hotel, dict)
        )

    if not accommodation_items:
        story.append(
            _paragraph(
                "Данные о проживании пока не добавлены. "
                "Перед выездом сохраните офлайн адрес, телефон, "
                "время заезда и номер бронирования.",
                styles["normal"],
            )
        )
    else:
        hotel_rows = [[
            _paragraph("Объект", styles["table_head"]),
            _paragraph("Адрес / место", styles["table_head"]),
            _paragraph("Контакты / заметка", styles["table_head"]),
        ]]

        for hotel in accommodation_items:
            name = _text(
                hotel.get("name")
                or hotel.get("title")
                or hotel.get("hotel"),
            )
            location = _text(
                hotel.get("address")
                or hotel.get("location")
                or hotel.get("city"),
            )
            note = _text(
                hotel.get("phone")
                or hotel.get("notes")
                or hotel.get("tip"),
            )

            hotel_rows.append(
                [
                    _paragraph(name, styles["table_cell_bold"]),
                    _paragraph(location, styles["table_cell"]),
                    _paragraph(note, styles["table_cell"]),
                ]
            )

        hotel_table = Table(
            hotel_rows,
            colWidths=[4.5 * cm, 6.0 * cm, 6.0 * cm],
            repeatRows=1,
        )
        hotel_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 7),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ]
            )
        )
        story.append(hotel_table)

    # ==========================================================
    # 5. БЮДЖЕТ И РАСХОДЫ
    # ==========================================================
    story.extend(_section_title("4. Бюджет и расходы", styles))

    planned_total = 0.0
    actual_total = 0.0

    for expense in expenses:
        amount = _money(_value(expense, "amount", 0))
        is_actual = bool(_value(expense, "is_actual", 0))

        if is_actual:
            actual_total += amount
        else:
            planned_total += amount

    budget_rows = [
        [
            _paragraph("Показатель", styles["table_head"]),
            _paragraph("Сумма", styles["table_head"]),
        ],
        [
            _paragraph("Общий бюджет поездки", styles["table_cell"]),
            _paragraph(
                _format_money(total_budget, currency),
                styles["table_cell_bold"],
            ),
        ],
        [
            _paragraph("Плановые расходы в системе", styles["table_cell"]),
            _paragraph(
                _format_money(planned_total, currency),
                styles["table_cell"],
            ),
        ],
        [
            _paragraph("Фактические расходы в системе", styles["table_cell"]),
            _paragraph(
                _format_money(actual_total, currency),
                styles["table_cell"],
            ),
        ],
        [
            _paragraph("Резерв относительно общего бюджета", styles["table_cell"]),
            _paragraph(
                _format_money(
                    max(_money(total_budget) - planned_total, 0),
                    currency,
                ),
                styles["table_cell"],
            ),
        ],
    ]

    budget_table = Table(
        budget_rows,
        colWidths=[11.7 * cm, 4.8 * cm],
        repeatRows=1,
    )
    budget_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.4, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    story.append(budget_table)

    # ==========================================================
    # 6. ЧЕК-ЛИСТ
    # ==========================================================
    story.extend(_section_title("5. Чек-лист подготовки", styles))

    for section_name, items in checklist_sections:
        story.append(
            Paragraph(section_name, styles["day"])
        )

        checklist_rows = []

        for item_text in items:
            item_key = checklist_key_builder(
                trip_id,
                section_name,
                item_text,
            )
            completed = checklist_statuses.get(item_key, False)

            status = "☑ Выполнено" if completed else "☐ Не выполнено"
            status_color = SUCCESS_COLOR if completed else MUTED_COLOR

            checklist_rows.append(
                [
                    _paragraph(
                        item_text,
                        styles["table_cell"],
                    ),
                    Paragraph(
                        status,
                        ParagraphStyle(
                            f"ChecklistStatus{len(checklist_rows)}",
                            parent=styles["table_cell"],
                            textColor=status_color,
                            alignment=TA_LEFT,
                        ),
                    ),
                ]
            )

        if checklist_rows:
            checklist_table = Table(
                checklist_rows,
                colWidths=[12.4 * cm, 4.1 * cm],
            )
            checklist_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                        ("GRID", (0, 0), (-1, -1), 0.35, BORDER_COLOR),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 8),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(checklist_table)
            story.append(Spacer(1, 0.16 * cm))

    # ==========================================================
    # 7. ЭКСТРЕННЫЕ ДАННЫЕ
    # ==========================================================
    story.extend(_section_title("6. Экстренные данные и офлайн-заметки", styles))

    story.append(
        _paragraph(
            "Заполните эти поля до поездки. TravelMind не добавляет "
            "контакты автоматически, потому что такие сведения должны "
            "быть подтверждены пользователем.",
            styles["normal"],
        )
    )
    story.append(Spacer(1, 0.15 * cm))

    emergency_rows = [
        [
            _paragraph("Экстренный номер", styles["table_cell_bold"]),
            _paragraph("112 / ______________________________", styles["table_cell"]),
        ],
        [
            _paragraph("Страховая компания и полис", styles["table_cell_bold"]),
            _paragraph("____________________________________", styles["table_cell"]),
        ],
        [
            _paragraph("Контакт близкого человека", styles["table_cell_bold"]),
            _paragraph("____________________________________", styles["table_cell"]),
        ],
        [
            _paragraph("Контакт проживания / трансфера", styles["table_cell_bold"]),
            _paragraph("____________________________________", styles["table_cell"]),
        ],
        [
            _paragraph("Важные лекарства / аллергии", styles["table_cell_bold"]),
            _paragraph("____________________________________", styles["table_cell"]),
        ],
    ]

    emergency_table = Table(
        emergency_rows,
        colWidths=[6.0 * cm, 10.5 * cm],
    )
    emergency_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), LIGHT_CYAN),
                ("BACKGROUND", (1, 0), (1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    story.append(emergency_table)

    document.build(
        story,
        onFirstPage=_footer,
        onLaterPages=_footer,
    )

    return buffer.getvalue()
