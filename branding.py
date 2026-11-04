import streamlit as st


def apply_clean_layout() -> None:
    """
    Скрывает служебные элементы Streamlit и применяет
    единый стеклянный стиль кнопок TravelMind.
    """
    st.markdown(
        """
        <style>
        /* ======================================================
           БАЗОВАЯ ОЧИСТКА ИНТЕРФЕЙСА STREAMLIT
           ====================================================== */

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

        /* ======================================================
           TRAVELMIND — КНОПКИ В СТИЛЕ МАТОВОГО СТЕКЛА
           ====================================================== */

        .stButton > button,
        .stFormSubmitButton > button,
        [data-testid="stLinkButton"] > a,
        [data-testid="stLinkButton"] a,
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

        [data-testid="stPageLink-NavLink"] p {
            margin: 0 !important;
            color: #F8FAFC !important;
            font-size: 0.95rem !important;
            font-weight: 700 !important;
        }

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

        .stButton > button:active,
        .stFormSubmitButton > button:active,
        [data-testid="stLinkButton"] > a:active,
        [data-testid="stLinkButton"] a:active,
        section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:active,
        [data-testid="stPageLink-NavLink"]:active {
            transform: translateY(0) scale(0.985) !important;
        }

        .stButton > button:focus-visible,
        .stFormSubmitButton > button:focus-visible,
        [data-testid="stLinkButton"] > a:focus-visible,
        [data-testid="stLinkButton"] a:focus-visible,
        section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:focus-visible,
        [data-testid="stPageLink-NavLink"]:focus-visible {
            outline: 2px solid rgba(125, 211, 252, 0.88) !important;
            outline-offset: 3px !important;
        }

        .stButton > button:disabled,
        .stFormSubmitButton > button:disabled {
            opacity: 0.46 !important;
            cursor: not-allowed !important;
            transform: none !important;
            box-shadow: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def show_author_mark() -> None:
    def apply_glass_buttons() -> None:
    """
    Повторно применяет стеклянный стиль кнопок.

    Вызывается после локального CSS страницы, если страница содержит
    старые яркие градиенты, которые перекрывают общий дизайн.
    """
    st.markdown(
        """
        <style>
        /* ======================================================
           TRAVELMIND — ПЕРЕОПРЕДЕЛЕНИЕ КНОПОК ПОСЛЕ CSS СТРАНИЦЫ
           ====================================================== */

        .stButton > button,
        .stFormSubmitButton > button,
        .stLinkButton > a,
        [data-testid="stLinkButton"] > a,
        [data-testid="stLinkButton"] a,
        section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"],
        [data-testid="stPageLink-NavLink"] {
            border: 1px solid rgba(255, 255, 255, 0.26) !important;
            border-radius: 15px !important;

            background: linear-gradient(
                135deg,
                rgba(255, 255, 255, 0.18) 0%,
                rgba(148, 163, 184, 0.11) 100%
            ) !important;

            color: #F8FAFC !important;
            font-weight: 700 !important;

            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.25),
                inset 0 -1px 0 rgba(15, 23, 42, 0.22),
                0 8px 22px rgba(0, 0, 0, 0.20) !important;

            backdrop-filter: blur(16px) saturate(140%);
            -webkit-backdrop-filter: blur(16px) saturate(140%);

            transition:
                transform 180ms ease,
                background 180ms ease,
                border-color 180ms ease,
                box-shadow 180ms ease !important;
        }

        /* Текст в навигационных кнопках Streamlit */
        [data-testid="stPageLink-NavLink"] p {
            margin: 0 !important;
            color: #F8FAFC !important;
            font-weight: 700 !important;
        }

        /* Основная кнопка отправки формы — заметнее, но всё ещё стекло */
        .stFormSubmitButton > button {
            border-color: rgba(165, 243, 252, 0.38) !important;

            background: linear-gradient(
                135deg,
                rgba(34, 211, 238, 0.24) 0%,
                rgba(99, 102, 241, 0.20) 100%
            ) !important;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover,
        .stLinkButton > a:hover,
        [data-testid="stLinkButton"] > a:hover,
        [data-testid="stLinkButton"] a:hover,
        section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:hover,
        [data-testid="stPageLink-NavLink"]:hover {
            transform: translateY(-1px) !important;
            border-color: rgba(186, 230, 253, 0.52) !important;

            background: linear-gradient(
                135deg,
                rgba(103, 232, 249, 0.25) 0%,
                rgba(167, 139, 250, 0.20) 100%
            ) !important;

            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.34),
                0 12px 28px rgba(34, 211, 238, 0.13),
                0 8px 20px rgba(0, 0, 0, 0.23) !important;
        }

        .stButton > button:active,
        .st
    """Показывает небольшую подпись автора внизу слева."""
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
            font-family: Inter, Arial, sans-serif !important;
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
