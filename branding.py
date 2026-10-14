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
        </style>

        <div class="tm-author-mark">Designed by Michael Degtyarev</div>
        """,
        unsafe_allow_html=True,
    )
