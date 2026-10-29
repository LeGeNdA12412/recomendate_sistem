import os
import sys
import requests
import streamlit as st
import pandas as pd

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.components.movie_card import render_movie_card, render_movie_grid
from app.ml_visualizations import (
    render_dataset_overview_tab,
    render_distribution_charts,
    render_model_evaluation_chart,
    render_pca_projection,
    render_similarity_heatmap,
    render_svd_scree_chart
)

API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="CineMatch AI — Рекомендательная система",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern UI without emojis/stickers
st.markdown("""
<style>
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }
    
    .status-badge-online {
        background-color: #064e3b;
        color: #34d399;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .status-badge-offline {
        background-color: #7f1d1d;
        color: #f87171;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
    }
    
    .page-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 0.3rem;
        color: #f9fafb;
    }
    .page-subtitle {
        color: #9ca3af;
        margin-bottom: 1.3rem;
        font-size: 0.92rem;
    }
</style>
""", unsafe_allow_html=True)


def call_api(endpoint: str, method: str = "GET", params: dict = None, json_data: dict = None):
    url = f"{API_BASE_URL.rstrip('/')}{endpoint}"
    try:
        if method.upper() == "GET":
            resp = requests.get(url, params=params, timeout=12)
        elif method.upper() == "POST":
            resp = requests.post(url, json=json_data, timeout=12)
        else:
            return None, f"Неподдерживаемый метод {method}"

        if resp.status_code in (200, 201):
            return resp.json(), None
        else:
            try:
                err_detail = resp.json().get("detail", resp.text)
            except Exception:
                err_detail = resp.text
            return None, f"Ошибка {resp.status_code}: {err_detail}"
    except requests.exceptions.ConnectionError:
        return None, "Не удалось подключиться к серверу API (http://127.0.0.1:8000)."
    except Exception as e:
        return None, str(e)

api_status, _ = call_api("/")
is_online = api_status is not None

users_data, _ = call_api("/api/users")
user_list = users_data if users_data else []
user_options = {u["id"]: f"{u['username']} ({u['ratings_count']} оценок)" for u in user_list}

top_col_brand, top_col_user = st.columns([3, 2])

with top_col_brand:
    st.markdown("""
        <div>
            <h2 style="margin: 0; padding: 0; font-size: 1.8rem; font-weight: 800; color: #60a5fa;">
                CineMatch AI
            </h2>
            <div style="color: #9ca3af; font-size: 0.85rem;">Интеллектуальная рекомендательная система фильмов</div>
        </div>
    """, unsafe_allow_html=True)

with top_col_user:
    u_c1, u_c2 = st.columns([2.5, 1.5])
    with u_c1:
        if user_options:
            selected_user_id = st.selectbox(
                "Активный пользователь:",
                options=list(user_options.keys()),
                format_func=lambda x: user_options[x],
                index=0,
                label_visibility="collapsed"
            )
            st.session_state["active_user_id"] = selected_user_id
        else:
            selected_user_id = None
            st.selectbox("Пользователь:", ["Загрузка..."], disabled=True, label_visibility="collapsed")
    with u_c2:
        if is_online:
            st.markdown(
                '<div style="text-align: right; padding-top: 5px;">'
                '<span class="status-badge-online">API Онлайн</span></div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div style="text-align: right; padding-top: 5px;">'
                '<span class="status-badge-offline">API Оффлайн</span></div>',
                unsafe_allow_html=True
            )
NAV_OPTIONS = [
    "Топ популярных",
    "Коллаборативная фильтрация",
    "По контенту (TF-IDF)",
    "Персональные (SVD)",
    "Оценить фильм",
    "Аналитика и Диаграммы",
    "Документация и API"
]

nav_choice = st.segmented_control(
    "Разделы приложения",
    options=NAV_OPTIONS,
    default=NAV_OPTIONS[0],
    label_visibility="collapsed"
)

if not nav_choice:
    nav_choice = NAV_OPTIONS[0]

st.markdown("<hr style='margin: 0.8rem 0 1.5rem 0; border-color: #374151;'>", unsafe_allow_html=True)

if nav_choice == "Топ популярных":
    st.markdown('<div class="page-title">Топ популярных фильмов</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Взвешенный байесовский рейтинг с учетом количества оценок и среднего балла по каталогу.</div>',
        unsafe_allow_html=True
    )

    col_f1, col_f2, col_f3 = st.columns([2, 1.5, 1])
    with col_f1:
        genres_data, _ = call_api("/api/movies/genres")
        genre_options = ["Все жанры"] + (genres_data if genres_data else [])
        chosen_genre = st.selectbox("Фильтр по жанру:", options=genre_options)
    with col_f2:
        limit_val = st.slider("Число фильмов (N):", min_value=5, max_value=30, value=10, step=1)
    with col_f3:
        view_mode = st.radio("Вид:", ["Сетка", "Список"], horizontal=True)

    genre_param = chosen_genre if chosen_genre != "Все жанры" else None
    params = {"limit": limit_val}
    if genre_param:
        params["genre"] = genre_param

    with st.spinner("Загрузка списка фильмов..."):
        data, err = call_api("/api/recommendations/popular", params=params)

    if err:
        st.error(err)
    elif data:
        recs = data.get("recommendations", [])
        st.success(f"Найдено фильмов: {len(recs)} (Жанр: {chosen_genre})")
        if view_mode == "Сетка":
            render_movie_grid(recs, show_score="weighted", cols_per_row=3)
        else:
            for movie in recs:
                render_movie_card(movie, rank=movie.get("rank"), show_score="weighted")

elif nav_choice == "Коллаборативная фильтрация":
    st.markdown('<div class="page-title">Коллаборативная фильтрация</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Алгоритмы на основе матрицы взаимодействий: сходство пользователей (User-Based) и сходство фильмов (Item-Based).</div>',
        unsafe_allow_html=True
    )

    cf_tab1, cf_tab2 = st.tabs(["По пользователям (User-Based)", "По фильмам (Item-Based)"])

    with cf_tab1:
        st.markdown("#### Рекомендации на основе похожих пользователей")
        st.caption("Поиск пользователей со схожими оценками через косинусное сходство и прогноз баллов.")

        if selected_user_id:
            c_u1, c_u2, c_u3 = st.columns([2.5, 1.5, 1])
            with c_u1:
                st.info(f"Активный профиль: {user_options.get(selected_user_id, 'User')} (ID: {selected_user_id})")
            with c_u2:
                ubcf_limit = st.slider("Лимит рекомендаций:", min_value=3, max_value=20, value=6, key="ubcf_lim")
            with c_u3:
                ub_view = st.radio("Вид:", ["Сетка", "Список"], horizontal=True, key="ub_view")

            with st.spinner("Расчет рекомендаций..."):
                ubcf_data, ubcf_err = call_api(
                    "/api/recommendations/collaborative/user-based",
                    params={"user_id": selected_user_id, "limit": ubcf_limit}
                )

            if ubcf_err:
                st.error(ubcf_err)
            elif ubcf_data:
                recs = ubcf_data.get("recommendations", [])
                st.success(f"Сформировано рекомендаций: {len(recs)}")
                if ub_view == "Сетка":
                    render_movie_grid(recs, show_score="predicted", cols_per_row=3)
                else:
                    for m in recs:
                        render_movie_card(m, rank=m.get("rank"), show_score="predicted")
        else:
            st.warning("Пользователи не найдены в базе данных.")

    with cf_tab2:
        st.markdown("#### Поиск похожих фильмов по профилю оценок")
        st.caption("Определение сходства фильмов на основе векторов оценок пользователей.")

        movies_data, _ = call_api("/api/movies", params={"limit": 100})
        movie_dict = {m["id"]: f"{m['title']} ({m.get('release_year', '—')}) [{m['genres']}]" for m in (movies_data or [])}

        if movie_dict:
            c_i1, c_i2, c_i3 = st.columns([2.5, 1.5, 1])
            with c_i1:
                target_movie_id = st.selectbox(
                    "Выберите исходный фильм:",
                    options=list(movie_dict.keys()),
                    format_func=lambda x: movie_dict[x],
                    index=0
                )
            with c_i2:
                ibcf_limit = st.slider("Число похожих фильмов:", min_value=3, max_value=15, value=6, key="ibcf_lim")
            with c_i3:
                ib_view = st.radio("Вид:", ["Сетка", "Список"], horizontal=True, key="ib_view")

            with st.spinner("Поиск похожих фильмов..."):
                ibcf_data, ibcf_err = call_api(
                    "/api/recommendations/collaborative/item-based",
                    params={"movie_id": target_movie_id, "limit": ibcf_limit}
                )

            if ibcf_err:
                st.error(ibcf_err)
            elif ibcf_data:
                recs = ibcf_data.get("recommendations", [])
                st.success(f"Найдено похожих фильмов: {len(recs)}")
                if ib_view == "Сетка":
                    render_movie_grid(recs, show_score="similarity", cols_per_row=3)
                else:
                    for m in recs:
                        render_movie_card(m, rank=m.get("rank"), show_score="similarity")


elif nav_choice == "По контенту (TF-IDF)":
    st.markdown('<div class="page-title">Фильтрация по контенту (Content-Based)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Векторизация текстовых метаданных (жанры, синопсис, режиссер, актеры) с помощью TF-IDF и косинусного расстояния.</div>',
        unsafe_allow_html=True
    )

    movies_data, _ = call_api("/api/movies", params={"limit": 100})
    movie_dict = {m["id"]: f"{m['title']} ({m.get('release_year', '—')}) — {m['genres']}" for m in (movies_data or [])}

    if movie_dict:
        col_cb1, col_cb2, col_cb3 = st.columns([2.5, 1.5, 1])
        with col_cb1:
            chosen_movie_id = st.selectbox(
                "Выберите фильм-эталон:",
                options=list(movie_dict.keys()),
                format_func=lambda x: movie_dict[x],
                index=0
            )
        with col_cb2:
            cb_limit = st.slider("Число рекомендаций:", min_value=3, max_value=20, value=6, key="cb_lim")
        with col_cb3:
            cb_view = st.radio("Вид:", ["Сетка", "Список"], horizontal=True, key="cb_view")

        with st.spinner("Расчет сходства контента..."):
            cb_data, cb_err = call_api(
                "/api/recommendations/content-based",
                params={"movie_id": chosen_movie_id, "limit": cb_limit}
            )

        if cb_err:
            st.error(cb_err)
        elif cb_data:
            recs = cb_data.get("recommendations", [])
            st.success(f"Сформировано рекомендаций: {len(recs)}")
            if cb_view == "Сетка":
                render_movie_grid(recs, show_score="similarity", cols_per_row=3)
            else:
                for m in recs:
                    render_movie_card(m, rank=m.get("rank"), show_score="similarity")


elif nav_choice == "Персональные (SVD)":
    st.markdown('<div class="page-title">Персональные гибридные рекомендации</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Синтез матричной факторизации (Truncated SVD) и контентного анализа с настройкой баланса α.</div>',
        unsafe_allow_html=True
    )

    if selected_user_id:
        c_p1, c_p2, c_p3 = st.columns([2, 1.5, 1])
        with c_p1:
            alpha_val = st.slider(
                "Баланс модели (α = история оценок SVD, 1-α = сходство сюжета):",
                min_value=0.0,
                max_value=1.0,
                value=0.65,
                step=0.05
            )
        with c_p2:
            p_limit = st.slider("Число рекомендаций:", min_value=3, max_value=20, value=6, key="p_lim")
        with c_p3:
            p_view = st.radio("Вид:", ["Сетка", "Список"], horizontal=True, key="p_view")

        with st.spinner("Построение персональных рекомендаций..."):
            p_data, p_err = call_api(
                "/api/recommendations/personal",
                params={"user_id": selected_user_id, "limit": p_limit, "alpha": alpha_val}
            )

        if p_err:
            st.error(p_err)
        elif p_data:
            recs = p_data.get("recommendations", [])
            st.success(f"Сформировано {len(recs)} персональных рекомендаций (α={alpha_val:.2f})")
            if p_view == "Сетка":
                render_movie_grid(recs, show_score="predicted", cols_per_row=3)
            else:
                for m in recs:
                    render_movie_card(m, rank=m.get("rank"), show_score="predicted")
    else:
        st.warning("Выберите пользователя в верхней панели.")


elif nav_choice == "Оценить фильм":
    st.markdown('<div class="page-title">Выставление оценки фильму (MySQL)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Добавление или обновление оценок с прямой записью в таблицы MySQL.</div>',
        unsafe_allow_html=True
    )

    if not selected_user_id:
        st.warning("Сначала выберите пользователя в верхней панели.")
    else:
        col_form, col_hist = st.columns([1.2, 1.8])

        with col_form:
            with st.container(border=True):
                st.markdown(f"#### Оценить фильм от имени: {user_options.get(selected_user_id)}")

                movies_data, _ = call_api("/api/movies", params={"limit": 100})
                movie_dict = {m["id"]: f"{m['title']} ({m.get('release_year', '—')})" for m in (movies_data or [])}

                if movie_dict:
                    with st.form("rating_form", clear_on_submit=False):
                        chosen_movie_id = st.selectbox(
                            "Выберите фильм:",
                            options=list(movie_dict.keys()),
                            format_func=lambda x: movie_dict[x]
                        )

                        score_input = st.select_slider(
                            "Оценка:",
                            options=[1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0],
                            value=5.0,
                            format_func=lambda x: f"{x:.1f}"
                        )

                        submit_btn = st.form_submit_button("Сохранить оценку в MySQL", use_container_width=True)

                    if submit_btn:
                        payload = {
                            "user_id": selected_user_id,
                            "movie_id": chosen_movie_id,
                            "rating": float(score_input)
                        }
                        with st.spinner("Запись в MySQL..."):
                            res, err = call_api("/api/ratings", method="POST", json_data=payload)

                        if err:
                            st.error(f"Ошибка сохранения: {err}")
                        elif res:
                            st.success(
                                f"Оценка успешно сохранена. Фильм: «{res.get('movie_title')}», балл: {res.get('rating')}"
                            )
                            st.rerun()

        with col_hist:
            with st.container(border=True):
                st.markdown("#### История оценок выбранного пользователя")
                user_ratings, ur_err = call_api(f"/api/ratings/user/{selected_user_id}")

                if user_ratings:
                    df_history = pd.DataFrame([
                        {
                            "ID": r["movie_id"],
                            "Название": r["movie_title"],
                            "Оценка": f"{r['rating']:.1f}",
                            "Дата и время (UTC)": r.get("timestamp", "—")[:19].replace("T", " ")
                        }
                        for r in user_ratings
                    ])
                    st.dataframe(df_history, use_container_width=True, height=350)
                else:
                    st.info("У этого пользователя пока нет сохраненных оценок.")


elif nav_choice == "Аналитика и Диаграммы":
    st.markdown('<div class="page-title">Аналитический дашборд (Столбчатые диаграммы)</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Все графики представлены в формате столбчатых диаграмм: разреженность, распределение оценок, жанры, метрики моделей, каменистая осыпь SVD, PCA и сходство фильмов.</div>',
        unsafe_allow_html=True
    )

    summary_data, _ = call_api("/api/analytics/summary")
    if summary_data:
        render_dataset_overview_tab(summary_data)

    st.markdown("<hr style='margin: 1.5rem 0; border-color: #374151;'>", unsafe_allow_html=True)

    r_dist, _ = call_api("/api/analytics/ratings-distribution")
    g_dist, _ = call_api("/api/analytics/genres-distribution")
    render_distribution_charts(r_dist, g_dist)

    st.markdown("<hr style='margin: 1.5rem 0; border-color: #374151;'>", unsafe_allow_html=True)

    eval_data, _ = call_api("/api/analytics/model-metrics")
    if eval_data:
        render_model_evaluation_chart(eval_data)

    st.markdown("<hr style='margin: 1.5rem 0; border-color: #374151;'>", unsafe_allow_html=True)

    scree_data, _ = call_api("/api/analytics/svd-scree")
    if scree_data:
        render_svd_scree_chart(scree_data)

    st.markdown("<hr style='margin: 1.5rem 0; border-color: #374151;'>", unsafe_allow_html=True)

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        pca_data, _ = call_api("/api/analytics/pca-projection")
        if pca_data:
            render_pca_projection(pca_data)

    with col_v2:
        sim_data, _ = call_api("/api/analytics/similarity-matrix")
        if sim_data:
            render_similarity_heatmap(sim_data)


elif nav_choice == "Документация и API":
    st.markdown('<div class="page-title">Документация и спецификация API</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="page-subtitle">Перечень эндпоинтов FastAPI, параметров запросов и форматов данных.</div>',
        unsafe_allow_html=True
    )

    col_info1, col_info2 = st.columns([3, 1])
    with col_info1:
        st.markdown(f"""
        Интерактивная песочница Swagger UI и спецификация ReDoc:
        - **Swagger UI:** [{API_BASE_URL}/docs]({API_BASE_URL}/docs)
        - **ReDoc:** [{API_BASE_URL}/redoc]({API_BASE_URL}/redoc)
        - **Статус сервиса:** [{API_BASE_URL}/]({API_BASE_URL}/)
        """)
    with col_info2:
        st.info("База данных: MySQL 9.x\n\nСервер: FastAPI / Uvicorn\n\nИнтерфейс: Streamlit")

    endpoints_documentation = [
        {
            "Метод": "GET",
            "Эндпоинт": "/api/recommendations/popular",
            "Назначение": "Топ популярных фильмов (взвешенный рейтинг)",
            "Параметры": "limit: int (def: 10), genre: str (опционально)"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/recommendations/collaborative/user-based",
            "Назначение": "User-Based коллаборативная фильтрация",
            "Параметры": "user_id: int (обяз.), limit: int (def: 10)"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/recommendations/collaborative/item-based",
            "Назначение": "Item-Based коллаборативная фильтрация",
            "Параметры": "movie_id: int (обяз.), limit: int (def: 10)"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/recommendations/content-based",
            "Назначение": "Контентные рекомендации по TF-IDF",
            "Параметры": "movie_id: int (обяз.), limit: int (def: 10)"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/recommendations/personal",
            "Назначение": "Персональный гибрид (SVD + Content)",
            "Параметры": "user_id: int, limit: int, alpha: float (0.0 - 1.0)"
        },
        {
            "Метод": "POST",
            "Эндпоинт": "/api/ratings",
            "Назначение": "Сохранить/обновить оценку фильма в MySQL",
            "Параметры": "JSON: {user_id, movie_id, rating: 1.0..5.0}"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/ratings/user/{user_id}",
            "Назначение": "История всех оценок пользователя",
            "Параметры": "user_id: int в пути запроса"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/movies",
            "Назначение": "Каталог фильмов с поиском и фильтром",
            "Параметры": "query: str, genre: str, skip: int, limit: int"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/analytics/summary",
            "Назначение": "Сводка данных и разреженность матрицы",
            "Параметры": "Без параметров"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/analytics/model-metrics",
            "Назначение": "Оценка моделей: RMSE, MAE, Precision, Recall",
            "Параметры": "Без параметров"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/analytics/svd-scree",
            "Назначение": "Каменистая осыпь SVD (Scree Plot)",
            "Параметры": "Без параметров"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/analytics/pca-projection",
            "Назначение": "2D проекция латентного пространства фильмов",
            "Параметры": "Без параметров"
        },
        {
            "Метод": "GET",
            "Эндпоинт": "/api/analytics/similarity-matrix",
            "Назначение": "Матрица попарного косинусного сходства",
            "Параметры": "Без параметров"
        }
    ]

    df_endpoints = pd.DataFrame(endpoints_documentation)
    st.dataframe(df_endpoints, use_container_width=True)
