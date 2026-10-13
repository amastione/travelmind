"""Страница истории поездок: список, открытие, удаление."""
import streamlit as st

import auth
import db

st.set_page_config(page_title="Мои поездки", page_icon="📚", layout="wide")

user_id = auth.require_auth()

st.title("📚 Мои поездки")

trips = db.list_trips(user_id)

if not trips:
    st.info("Пока нет ни одной поездки.")
    st.page_link("pages/1_new_trip.py", label="Создать первую →")
    st.stop()

st.caption(f"Всего поездок: {len(trips)}")

for t in trips:
    with st.container(border=True):
        c1, c2, c3, c4 = st.columns([3, 2, 1, 1])

        c1.markdown(f"### {t['title']}")
        c1.caption(
            f"{t['destination']} · {t['start_date']} — {t['end_date']} · "
            f"{t['people']} чел."
        )
        c2.metric("Бюджет", f"{t['budget']:.0f} {t['currency']}")

        if c3.button("Открыть", key=f"open_{t['id']}"):
            st.session_state["current_trip_id"] = t["id"]
            st.switch_page("pages/3_trip_detail.py")

        if c4.button("Удалить", key=f"del_{t['id']}"):
            db.delete_trip(t["id"], user_id)
            st.toast(f"Поездка «{t['title']}» удалена")
            st.rerun()
