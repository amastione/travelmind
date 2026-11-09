"""Страница AI-подбора направлений для короткой поездки."""

import json
from html import escape

import streamlit as st

import ai
import auth
import branding
import site_access


st.set_page_config(
    page_title="Идеи для поездки",
    page_icon="✨",
    layout="wide",
)

branding.apply_clean_layout()
site_access.require_site_access()
user_id = auth.require_auth()


CSS = """
<style>
.stApp {
    background:
        radial-gradient(
            circle at 10% 8%,
            rgba(34, 211, 238, 0.12),
            transparent 28%
        ),
        radial-gradient(
            circle at 90% 88%,
            rgba(139, 92, 246, 0.15),
            transparent 36%
        ),
        linear-gradient(
            135deg,
            #070B14 0%,
            #0D1628 50%,
            #101426 100%
        );
    color: #F4F7FB;
}

.block-container {
    max-width: 1180px;
    padding-top: 2.5rem;
    padding-bottom: 4rem;
}

#MainMenu,
footer {
    visibility: hidden;
}

.tm-page-eyebrow {
    color: #67E8F9;
    font-size: 0.82rem;
    font-weight: 750;
    letter-spacing: 0.09rem;
    text-transform: uppercase;
}

.tm-page-title {
    margin: 0.35rem 0 0 !important;
    color: #F8FAFC !important;
    font-size: 2.45rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.06rem;
}

.tm-page-description {
    margin: 0.7rem 0 1.5rem;
    color: #AAB8CE;
    font-size: 1.05rem;
    line-height: 1.6;
}

.tm-info-card {
    margin: 1rem 0 1.4rem;
    padding: 1rem 1.15rem;
    border: 1px solid rgba(34, 211, 238, 0.20);
    border-radius: 16px;
    background: rgba(34, 211, 238, 0.06);
    color: #C9D7E8;
    line-height: 1.55;
}

[data-testid="stForm"] {
    padding: 1.6rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 22px;
    background: rgba(15, 23, 42, 0.72);
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.25);
}

.tm-result-summary {
    margin: 1.6rem 0 1rem;
    padding: 1rem 1.15rem;
    border: 1px solid rgba(125, 211, 252, 0.24);
    border-radius: 16px;
    background: rgba(30, 41, 59, 0.62);
    color: #DCE8F8;
    line-height: 1.55;
}

.tm-idea-card {
    min-height: 270px;
    margin-bottom: 0.35rem;
    padding: 1.25rem;
    border: 1px solid rgba(148, 163, 184, 0.20);
    border-radius: 20px;
    background:
        linear-gradient(
            135deg,
            rgba(30, 41, 59, 0.72),
            rgba(15, 23, 42, 0.80)
        );
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.06),
        0 12px 30px rgba(0, 0, 0, 0.15);
}

.tm-idea-title {
    color: #F8FAFC;
    font-size: 1.22rem;
    font-weight: 800;
    line-height: 1.28;
}

.tm-idea-place {
    margin-top: 0.38rem;
    color: #9FB2CB;
    font-size: 0.92rem;
}

.tm-idea-meta {
    margin-top: 0.85rem;
    color: #C7D7E9;
    font-size: 0.9rem;
    line-height: 1.7;
}

.tm-idea-why {
    margin-top: 0.85rem;
    color: #E4EDF8;
    font-size: 0.94rem;
    line-height: 1.55;
}

.tm-idea-highlights {
    margin: 0.8rem 0 0;
    padding-left: 1.1rem;
    color: #AABDD4;
    font-size: 0.9rem;
    line-height: 1.55;
}

.tm-caution {
    margin-top
