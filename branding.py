import streamlit as st


def apply_clean_layout() -> None:
    """Скрывает служебные элементы Streamlit."""
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
    """Показывает подпись автора в левом нижнем углу."""
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
    """Применяет стеклянный стиль после локального CSS страницы."""
    st.markdown(
        """
        <style>
        .stButton > button,
        .stFormSubmitButton > button,
        .stLinkButton > a,
        [data-testid="stLinkButton"] > a,
        [data-testid="stLinkButton"] a,
        section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"],
        [data-testid="stPageLink-NavLink"] {
            border: 1px solid rgba(255, 255, 255, 0.26) !important;
            border-radius: 15px !important;

            background: rgba(255, 255, 255, 0.14) !important;

            color: #F8FAFC !important;
            font-weight: 700 !important;
            text-decoration: none !important;

            box-shadow:
                inset 0 1px 0 rgba(255, 255, 255, 0.22),
                inset 0 -1px 0 rgba(15, 23, 42, 0.20),
                0 8px 22px rgba(0, 0, 0, 0.20) !important;

            backdrop-filter: blur(16px) saturate(140%);
            -webkit-backdrop-filter: blur(16px) saturate(140%);

            transition:
                transform 180ms ease,
                background 180ms ease,
                border-color 180ms ease !important;
        }

        [data-testid="stPageLink-NavLink"] p {
            margin: 0 !important;
            color: #F8FAFC !important;
            font-weight: 700 !important;
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
            background: rgba(103, 232, 249, 0.18) !important;
        }

        .stButton > button:active,
        .stFormSubmitButton > button:active,
        .stLinkButton > a:active,
        [data-testid="stLinkButton"] > a:active,
        [data-testid="stLinkButton"] a:active,
        section[data-testid="stMain"] a[data-testid="stPageLink-NavLink"]:active,
        [data-testid="stPageLink-NavLink"]:active {
            transform: scale(0.985) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
