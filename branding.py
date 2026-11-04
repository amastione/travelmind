import streamlit as st


def apply_clean_layout() -> None:
    """Скрывает стандартные элементы Streamlit: шапку и боковую панель."""
    st.markdown(
        """
        <style>
        /* Верхняя служебная панель Streamlit */
        [data-testid="stHeader"] {
            display: none !important;
        }

        /* Меню с тремя точками и служебная панель */
        [data-testid="stToolbar"] {
            display: none !important;
        }

        /* Левая боковая панель Streamlit */
        [data-testid="stSidebar"] {
            display: none !important;
        }

        /* Кнопка открытия скрытой боковой панели */
        [data-testid="collapsedControl"] {
            display: none !important;
        }

        /* Убираем пустой отступ, который остаётся после скрытия шапки */
        .block-container {
            padding-top: 2.2rem !important;
        }

        /* На телефонах чуть уменьшаем верхний отступ */
        @media (max-width: 700px) {
            .block-container {
                padding-top: 1.4rem !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_author_mark() -> None:
    """Небольшая подпись автора в левом нижнем углу."""
    st.markdown(
        """
        <style>
        div.tm-author-mark {
            position: fixed !important;
            left: 18px !important;
            right: auto !important;
            bottom: 16px !important;
            top: auto !important;

            z-index: 999999 !important;
            margin: 0 !important;
            padding: 0 !important;

            color: rgba(148, 163, 184, 0.62) !important;
            font-family: Inter, Arial, sans-serif !important;
            font-size: 12px !important;
            font-weight: 400 !important;
            line-height: 1.2 !important;
            letter-spacing: 0.02em !important;
            text-transform: none !important;
            white-space: nowrap !important;

            pointer-events: none !important;
            user-select: none !important;
        }

        div.tm-author-mark,
        div.tm-author-mark * {
            color: rgba(148, 163, 184, 0.62) !important;
            font-family: Inter, Arial, sans-serif !important;
            font-size: 12px !important;
            font-weight: 400 !important;
            text-transform: none !important;
        }

        @media (max-width: 700px) {
            div.tm-author-mark {
                left: 12px !important;
                bottom: 12px !important;
                font-size: 10px !important;
            }

            div.tm-author-mark,
            div.tm-author-mark * {
                font-size: 10px !important;
            }
        }
        /* Скрываем элементы управления Streamlit Cloud */
            [data-testid="stStatusWidget"] {
                display: none !important;
            }
            
            [data-testid="stDeployButton"] {
                display: none !important;
            }
            
            [data-testid="manage-app-button"] {
                display: none !important;
            }
            /* ==========================================================
   TRAVELMIND — УНИВЕРСАЛЬНЫЕ КНОПКИ В СТИЛЕ МАТОВОГО СТЕКЛА
   Применяется ко всем страницам, использующим apply_clean_layout()
   ========================================================== */

/* Обычные кнопки и кнопки внутри форм */
.stButton > button,
.stFormSubmitButton > button {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;

    min-height: 46px !important;
    padding: 0.68rem 1rem !important;

    border: 1px solid rgba(255, 255, 255, 0.20) !important;
    border-radius: 14px !important;

    background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.16) 0%,
        rgba(148, 163, 184, 0.10) 100%
    ) !important;

    color: #F8FAFC !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;

    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.18),
        inset 0 -1px 0 rgba(15, 23, 42, 0.20),
        0 8px 22px rgba(0, 0, 0, 0.16) !important;

    backdrop-filter: blur(14px) saturate(130%);
    -webkit-backdrop-filter: blur(14px) saturate(130%);

    transition:
        transform 180ms ease,
        background 180ms ease,
        border-color 180ms ease,
        box-shadow 180ms ease !important;
}

/* Внешние кнопки: карты, билеты, отели и др. */
[data-testid="stLinkButton"] > a,
[data-testid="stLinkButton"] a {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;

    min-height: 46px !important;
    padding: 0.68rem 1rem !important;

    border: 1px solid rgba(255, 255, 255, 0.20) !important;
    border-radius: 14px !important;

    background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.16) 0%,
        rgba(148, 163, 184, 0.10) 100%
    ) !important;

    color: #F8FAFC !important;
    text-decoration: none !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;

    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.18),
        inset 0 -1px 0 rgba(15, 23, 42, 0.20),
        0 8px 22px rgba(0, 0, 0, 0.16) !important;

    backdrop-filter: blur(14px) saturate(130%);
    -webkit-backdrop-filter: blur(14px) saturate(130%);

    transition:
        transform 180ms ease,
        background 180ms ease,
        border-color 180ms ease,
        box-shadow 180ms ease !important;
}

/* Навигационные кнопки Streamlit: Главное меню, Мои поездки и т. д. */
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"],
[data-testid="stPageLink-NavLink"] {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;

    min-height: 46px !important;
    padding: 0.68rem 1rem !important;

    border: 1px solid rgba(255, 255, 255, 0.20) !important;
    border-radius: 14px !important;

    background: linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.16) 0%,
        rgba(148, 163, 184, 0.10) 100%
    ) !important;

    color: #F8FAFC !important;
    text-decoration: none !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;

    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.18),
        inset 0 -1px 0 rgba(15, 23, 42, 0.20),
        0 8px 22px rgba(0, 0, 0, 0.16) !important;

    backdrop-filter: blur(14px) saturate(130%);
    -webkit-backdrop-filter: blur(14px) saturate(130%);

    transition:
        transform 180ms ease,
        background 180ms ease,
        border-color 180ms ease,
        box-shadow 180ms ease !important;
}

/* Текст внутри кнопок-ссылок навигации */
[data-testid="stPageLink-NavLink"] p {
    margin: 0 !important;
    color: #F8FAFC !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
}

/* Общее состояние при наведении */
.stButton > button:hover,
.stFormSubmitButton > button:hover,
[data-testid="stLinkButton"] > a:hover,
[data-testid="stLinkButton"] a:hover,
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:hover,
[data-testid="stPageLink-NavLink"]:hover {
    transform: translateY(-1px) !important;
    border-color: rgba(186, 230, 253, 0.48) !important;

    background: linear-gradient(
        135deg,
        rgba(103, 232, 249, 0.20) 0%,
        rgba(167, 139, 250, 0.16) 100%
    ) !important;

    color: #FFFFFF !important;

    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.30),
        0 12px 28px rgba(34, 211, 238, 0.12),
        0 8px 20px rgba(0, 0, 0, 0.20) !important;
}

/* Эффект лёгкого нажатия */
.stButton > button:active,
.stFormSubmitButton > button:active,
[data-testid="stLinkButton"] > a:active,
[data-testid="stLinkButton"] a:active,
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:active,
[data-testid="stPageLink-NavLink"]:active {
    transform: translateY(0) scale(0.985) !important;
}

/* Выделение при навигации клавиатурой */
.stButton > button:focus-visible,
.stFormSubmitButton > button:focus-visible,
[data-testid="stLinkButton"] > a:focus-visible,
[data-testid="stLinkButton"] a:focus-visible,
section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:focus-visible,
[data-testid="stPageLink-NavLink"]:focus-visible {
    outline: 2px solid rgba(125, 211, 252, 0.88) !important;
    outline-offset: 3px !important;
}

/* Неактивные кнопки */
.stButton > button:disabled,
.stFormSubmitButton > button:disabled {
    opacity: 0.46 !important;
    cursor: not-allowed !important;
    transform: none !important;
    box-shadow: none !important;
}
        </style>

        <div class="tm-author-mark">Designed by Michael Degtyarev</div>
        """,
        unsafe_allow_html=True,
    )
