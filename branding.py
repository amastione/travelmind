import streamlit as st


def show_author_mark() -> None:
    """Маленькая подпись автора в правом верхнем углу."""
    st.markdown(
        """
        <style>
        /* Контейнер подписи — фиксированно в правом верхнем углу экрана */
        div.tm-author-mark {
            position: fixed !important;
            top: 14px !important;
            right: 62px !important;
            left: auto !important;
            bottom: auto !important;

            z-index: 999999 !important;
            margin: 0 !important;
            padding: 0 !important;

            color: rgba(148, 163, 184, 0.58) !important;
            font-family: Inter, Arial, sans-serif !important;
            font-size: 10px !important;
            font-weight: 400 !important;
            line-height: 1 !important;
            letter-spacing: 0.02em !important;
            text-transform: none !important;
            white-space: nowrap !important;

            pointer-events: none !important;
            user-select: none !important;
        }

        /* Защита от глобальных CSS-стилей приложения */
        div.tm-author-mark,
        div.tm-author-mark * {
            color: rgba(148, 163, 184, 0.58) !important;
            font-size: 10px !important;
            font-weight: 400 !important;
            text-transform: none !important;
        }

        @media (max-width: 700px) {
            div.tm-author-mark {
                top: 12px !important;
                right: 48px !important;
                font-size: 8px !important;
            }

            div.tm-author-mark,
            div.tm-author-mark * {
                font-size: 8px !important;
            }
        }
        </style>

        <div class="tm-author-mark">Designed by Michael Degtyarev</div>
        """,
        unsafe_allow_html=True,
    )
