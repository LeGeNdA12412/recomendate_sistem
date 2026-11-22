import os
import requests
import streamlit as st
import recommender as r
from db import get_connection

st.set_page_config(page_title="Рекомендательная система фильмов", layout="wide")

API_URL = "http://127.0.0.1:8000"


def check_api():
    try:
        res = requests.get(f"{API_URL}/", timeout=0.8)
        return res.status_code == 200
    except Exception:
        return False


def get_poster_path(movie_id):
    path = os.path.join("posters", f"{movie_id}.jpg")
    if os.path.exists(path):
        return path
    return None


def render_movies(movies_list):
    if not movies_list:
        st.write("Список пуст.")
        return

    cols = st.columns(5)
    for idx, movie in enumerate(movies_list):
        with cols[idx % 5]:
            poster = get_poster_path(movie["id"])
            if poster:
                st.image(poster, use_container_width=True)
            st.write(f"**{movie['title']}** ({movie['release_year']})")
            
            if "votes" in movie and movie["votes"] > 0:
                st.write(f"Рейтинг: {movie['rating']} (оценок: {movie['votes']})")
            else:
                st.write(f"Рейтинг: {movie.get('rating', '-')}")

            if "similarity" in movie:
                st.write(f"Сходство: {movie['similarity']}%")

            st.write(f"Жанры: {movie['genres']}")
            with st.expander("Описание"):
                st.write(movie.get("description", "Нет описания"))


api_online = check_api()

with st.sidebar:
    st.subheader("Меню")
    mode = st.radio(
        "Раздел:",
        [
            "Топ-10 популярных",
            "Коллаборативная фильтрация",
            "По контенту",
            "Персональные рекомендации",
            "Оценить фильм",
            "Справка"
        ]
    )
    st.write("---")
    if api_online:
        st.write("Режим: API (порт 8000)")
    else:
        st.write("Режим: Прямое подключение к БД")

st.title("Рекомендательная система фильмов")

if mode == "Топ-10 популярных":
    st.subheader("Топ-10 популярных фильмов")
    if api_online:
        try:
            movies = requests.get(f"{API_URL}/api/popular?count=10").json()
        except Exception:
            movies = r.get_top_popular(10)
    else:
        movies = r.get_top_popular(10)
    render_movies(movies)

elif mode == "Коллаборативная фильтрация":
    st.subheader("Коллаборативная фильтрация")
    sub_mode = st.radio("Тип:", ["По фильмам", "По пользователям"], horizontal=True)

    all_movies = r.get_all_movies()
    all_titles = [m["title"] for m in all_movies]
    all_users = r.get_all_users()

    if sub_mode == "По фильмам":
        selected_title = st.selectbox("Фильм:", all_titles)
        if api_online:
            try:
                recs = requests.get(f"{API_URL}/api/collaborative/movie", params={"title": selected_title, "count": 10}).json()
            except Exception:
                recs = r.get_collaborative_by_movie(selected_title, top_n=10)
        else:
            recs = r.get_collaborative_by_movie(selected_title, top_n=10)
        render_movies(recs)
    else:
        selected_user = st.selectbox("ID пользователя:", all_users)
        if api_online:
            try:
                recs = requests.get(f"{API_URL}/api/collaborative/user", params={"user_id": selected_user, "count": 10}).json()
            except Exception:
                recs = r.get_collaborative_by_user(selected_user, top_n=10)
        else:
            recs = r.get_collaborative_by_user(selected_user, top_n=10)
        render_movies(recs)

elif mode == "По контенту":
    st.subheader("Рекомендации по контенту")
    all_movies = r.get_all_movies()
    all_titles = [m["title"] for m in all_movies]
    selected_title = st.selectbox("Фильм:", all_titles)

    if api_online:
        try:
            recs = requests.get(f"{API_URL}/api/content-based", params={"title": selected_title, "count": 10}).json()
        except Exception:
            recs = r.get_content_based(selected_title, top_n=10)
    else:
        recs = r.get_content_based(selected_title, top_n=10)
    render_movies(recs)

elif mode == "Персональные рекомендации":
    st.subheader("Персональные рекомендации")
    all_users = r.get_all_users()
    selected_user = st.selectbox("ID пользователя:", all_users)

    if api_online:
        try:
            recs = requests.get(f"{API_URL}/api/personal", params={"user_id": selected_user, "count": 10}).json()
        except Exception:
            recs = r.get_personal_recommendations(selected_user, top_n=10)
    else:
        recs = r.get_personal_recommendations(selected_user, top_n=10)
    render_movies(recs)

elif mode == "Оценить фильм":
    st.subheader("Оценка фильма")
    all_movies = r.get_all_movies()
    movie_dict = {m["title"]: m["id"] for m in all_movies}

    col1, col2 = st.columns(2)
    with col1:
        user_id = st.number_input("ID пользователя:", min_value=1, max_value=1000, value=1)
        selected_movie_title = st.selectbox("Фильм:", list(movie_dict.keys()))
        rating_score = st.slider("Оценка:", min_value=1.0, max_value=5.0, value=4.5, step=0.5)

        if st.button("Сохранить"):
            movie_id = movie_dict[selected_movie_title]
            saved = False
            if api_online:
                try:
                    payload = {"user_id": int(user_id), "movie_id": int(movie_id), "rating": float(rating_score)}
                    res = requests.post(f"{API_URL}/api/rate", json=payload)
                    saved = res.status_code == 200
                except Exception:
                    saved = r.rate_movie(int(user_id), int(movie_id), float(rating_score))
            else:
                saved = r.rate_movie(int(user_id), int(movie_id), float(rating_score))

            if saved:
                st.success("Оценка сохранена в базу данных.")
            else:
                st.error("Ошибка при сохранении.")

    with col2:
        m_id = movie_dict[selected_movie_title]
        poster = get_poster_path(m_id)
        if poster:
            st.image(poster, width=220)

elif mode == "Справка":
    st.subheader("Справка по командам API")
    help_data = [
        {"Команда": "GET /api/popular", "Параметры": "count (int)", "Описание": "Список популярных фильмов"},
        {"Команда": "GET /api/collaborative/movie", "Параметры": "title (str), count (int)", "Описание": "Фильтрация по похожим фильмам"},
        {"Команда": "GET /api/collaborative/user", "Параметры": "user_id (int), count (int)", "Описание": "Фильтрация по схожим пользователям"},
        {"Команда": "GET /api/content-based", "Параметры": "title (str), count (int)", "Описание": "10 рекомендаций по контенту"},
        {"Команда": "GET /api/personal", "Параметры": "user_id (int), count (int)", "Описание": "Персональные рекомендации"},
        {"Команда": "POST /api/rate", "Параметры": "user_id, movie_id, rating", "Описание": "Сохранить оценку фильма"},
        {"Команда": "GET /api/help", "Параметры": "-", "Описание": "Справка по API"}
    ]
    st.table(help_data)
    st.write("Документация Swagger: http://127.0.0.1:8000/docs")
