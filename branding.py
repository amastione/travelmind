import streamlit as st


def show_author_mark() -> None:
    """Небольшая подпись об авторстве в правом верхнем углу."""
    st.markdown(
        """
        <style>
        .tm-author-mark {
            position: fixed;
            top: 12px;
            right: 56px;
            z-index: 999;
            color: rgba(148, 163, 184, 0.62);
            font-size: 0.66rem;
            font-weight: 500;
            letter-spacing: 0.025em;
            line-height: 1;
            pointer-events: none;
            user-select: none;
        }

        @media (max-width: 700px) {
            .tm-author-mark {
                top: 10px;
                right: 48px;
                font-size: 0.56rem;
            }
        }
        </style>

        <div class="tm-author">
          Concept & design by <strong>Michael Degtyarev</strong>
        </div>
        """,
        unsafe_allow_html=True,
    )
