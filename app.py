"""TravelMind — главная страница: вход и регистрация."""
import streamlit as st

import auth
import db

st.set_page_config(
    page_title="TravelMind — AI-планировщик путешествий",
    page_icon="🗺️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Инициализация базы данных
db.init()

# ---------- СТИЛИ ----------

st.markdown(
    """
    <style>
        /* ---------- ОСНОВНОЙ ФОН ---------- */

        .stApp {
            background:
                radial-gradient(
                    circle at 12% 12%,
                    rgba(34, 211, 238, 0.16) 0%,
                    transparent 30%
                ),
                radial-gradient(
                    circle at 90% 85%,
                    rgba(139, 92, 246, 0.18) 0%,
                    transparent 35%
                ),
                linear-gradient(
                    135deg,
                    #070B14 0%,
                    #0D1628 52%,
                    #101426 100%
                );
            color: #F4F7FB;
        }

        .block-container {
            max-width: 760px;
            padding-top: 4.2rem;
            padding-bottom: 4rem;
        }

        #MainMenu {
            visibility: hidden;
        }

        footer {
            visibility: hidden;
        }

        h1, h2, h3 {
            color: #F8FAFC !important;
        }

        /* ---------- ЛОГОТИП TRAVELMIND ---------- */

        .tm-logo-wide {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.35rem;
            width: fit-content;
            max-width: 100%;
            margin: 0 auto 1.2rem;
            padding: 1.05rem 1.55rem;
            border: 1px solid rgba(34, 211, 238, 0.28);
            border-radius: 22px;
            background:
                linear-gradient(
                    135deg,
                    rgba(10, 29, 53, 0.84),
                    rgba(12, 22, 45, 0.72)
                );
            box-shadow:
                0 20px 55px rgba(0, 0, 0, 0.28),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }

        .tm-map-symbol {
            position: relative;
            width: 105px;
            height: 84px;
            flex: 0 0 105px;
        }

        /* Сложенная карта */
        .tm-map-left,
        .tm-map-center,
        .tm-map-right {
            position: absolute;
            bottom: 5px;
            height: 43px;
            transform: skewY(18deg);
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.20);
        }

        .tm-map-left {
            left: 4px;
            width: 34px;
            border-radius: 5px 0 0 5px;
            background: linear-gradient(145deg, #25CDED, #168DE6);
        }

        .tm-map-center {
            left: 37px;
            width: 34px;
            background: linear-gradient(145deg, #168EEA, #2778DA);
        }

        .tm-map-right {
            left: 70px;
            width: 32px;
            border-radius
