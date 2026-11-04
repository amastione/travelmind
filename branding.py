import streamlit as st


def apply_clean_layout() -> None:
    """Скрывает служебные элементы интерфейса Streamlit."""
    st.markdown(
        """
        <style>
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        [data-testid="stStatusWidget"],
        [data-testid="stDeployButton"],
        [data-testid="manage-app-button"] {
            display: none !important;
        }

        .block-container {
            padding-top: 2.2rem !important;
        }

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
    """Выводит подпись автора в левом нижнем углу."""
    st.markdown(
        """
        <style>
        .tm-author-mark {
            position: fixed !important;
            left: 18px !important;
            bottom: 16px !important;
            z-index: 999999 !important;

            margin: 0 !important;
            padding: 0 !important;

            color: rgba(148, 163, 184, 0.62) !important;
            font-family: Arial, sans-serif !important;
            font-size: 12px !important;
            font-weight: 400 !important;
            line-height: 1.2 !important;
            letter-spacing: 0.02em !important;
            white-space: nowrap !important;

            pointer-events: none !important;
            user-select: none !important;
        }

        @media (max-width: 700px) {
            .tm-author-mark {
                left: 12px !important;
                bottom: 12px !important;
                font-size: 10px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="tm-author-mark">Designed by Michael Degtyarev</div>',
        unsafe_allow_html=True,
    )


def apply_glass_buttons() -> None:
    """Переопределяет старые градиенты кнопок после CSS страницы."""
    st.markdown(
