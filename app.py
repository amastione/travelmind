"""TravelMind — главная страница: вход и регистрация."""
import streamlit as st

import auth
import db

st.set_page_config(page_title="TravelMind", page_icon="🧭", layout="centered")

# Явный вызов — страховка на случай, если init() не сработал при импорте
db.init()

st.title("🧭 TravelMind")
st.caption("AI-планировщик путешествий · учебный MVP")

# ---------- Если пользователь уже вошёл ----------
if "user_id" in st.session_state:
    st.success(f"Вы вошли как **{st.session_state['username']}**")
    st.page_link("pages/1_new_trip.py", label="📝 Создать поездку")
    st.page_link("pages/2_my_trips.py", label="📚 Мои поездки")
    if st.button("Выйти"):
        auth.logout()
        st.rerun()
    st.stop()

# ---------- Иначе показываем форму входа ----------
tab_login, tab_register = st.tabs(["Вход", "Регистрация"])

with tab_login:
    with st.form("login_form"):
        u = st.text_input("Логин")
        p = st.text_input("Пароль", type="password")
        if st.form_submit_button("Войти"):
            err = auth.login(u, p)
            if err:
                st.error(err)
            else:
                st.rerun()

with tab_register:
    with st.form("register_form"):
        u = st.text_input("Логин", key="r_u")
        p = st.text_input("Пароль", type="password", key="r_p")
        p2 = st.text_input("Повторите пароль", type="password", key="r_p2")
        if st.form_submit_button("Зарегистрироваться"):
            if p != p2:
                st.error("Пароли не совпадают.")
            else:
                err = auth.register(u, p)
                if err:
                    st.error(err)
                else:
                    auth.login(u, p)
                    st.rerun()
