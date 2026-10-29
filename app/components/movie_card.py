import os
import streamlit as st

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def resolve_poster_path(movie: dict):
    poster = movie.get("poster_url")
    if poster:
        if os.path.isabs(poster) and os.path.exists(poster):
            return poster
        rel = os.path.join(PROJECT_ROOT, poster)
        if os.path.exists(rel):
            return rel
        if poster.startswith(("http://", "https://")):
            return poster

    m_id = movie.get("id")
    if m_id:
        for ext in (".jpg", ".png", ".jpeg"):
            fallback = os.path.join(PROJECT_ROOT, "app", "static", "posters", f"{m_id}{ext}")
            if os.path.exists(fallback):
                return fallback

    title = movie.get("title")
    if title:
        safe_title = title.replace(":", "").replace("/", "_").replace("«", "").replace("»", "").strip()
        for ext in (".jpg", ".png", ".jpeg"):
            fallback = os.path.join(PROJECT_ROOT, "app", "static", "posters", f"{safe_title}{ext}")
            if os.path.exists(fallback):
                return fallback

    return None


def render_movie_card(movie: dict, rank: int = None, show_score: str = None, key_prefix: str = ""):
    """Отрисовка подробной карточки фильма в виде строки без эмодзи."""
    poster_path = resolve_poster_path(movie)
    avg = movie.get("avg_rating", 0.0) or 0.0
    cnt = movie.get("ratings_count", 0) or 0
    genres = movie.get("genres", "") or ""
    genre_list = [g.strip() for g in genres.split(",") if g.strip()]
    year_str = f" ({movie.get('release_year')})" if movie.get("release_year") else ""
    rank_str = f"#{rank} " if rank else ""

    with st.container(border=True):
        col_img, col_info = st.columns([1, 4])

        with col_img:
            if poster_path:
                st.image(poster_path, use_container_width=True)
            else:
                st.markdown(
                    """
                    <div style="background: #1f2937; height: 220px; border-radius: 8px;
                                display: flex; align-items: center; justify-content: center; color: #9ca3af;">
                        Нет постера
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col_info:
            st.markdown(f"### {rank_str}{movie.get('title')}{year_str}")

            b_cols = st.columns([1.2, 1.2, 2.6])

            with b_cols[0]:
                st.markdown(f"**Средний балл: {avg:.2f}** / 5.0")
                st.caption(f"Оценок: {cnt}")

            with b_cols[1]:
                if show_score == "weighted" and movie.get("weighted_score") is not None:
                    st.markdown(
                        f"""<span style="background: #b45309; color: white; padding: 4px 10px; border-radius: 8px; font-weight: 600;">
                        Рейтинг: {movie.get('weighted_score'):.2f}</span>""",
                        unsafe_allow_html=True
                    )
                elif show_score == "predicted" and movie.get("predicted_rating") is not None:
                    st.markdown(
                        f"""<span style="background: #047857; color: white; padding: 4px 10px; border-radius: 8px; font-weight: 600;">
                        Прогноз: {movie.get('predicted_rating'):.2f} / 5</span>""",
                        unsafe_allow_html=True
                    )
                elif show_score == "similarity" and movie.get("similarity_score") is not None:
                    sim_pct = movie.get('similarity_score') * 100
                    st.markdown(
                        f"""<span style="background: #6d28d9; color: white; padding: 4px 10px; border-radius: 8px; font-weight: 600;">
                        Сходство: {sim_pct:.1f}%</span>""",
                        unsafe_allow_html=True
                    )
                else:
                    st.caption("Поиск")

            with b_cols[2]:
                chips_html = " ".join([
                    f'<span style="background-color: #374151; color: #f3f4f6; '
                    f'padding: 3px 8px; border-radius: 6px; font-size: 0.8rem; margin-right: 4px;">{g}</span>'
                    for g in genre_list
                ])
                st.markdown(chips_html, unsafe_allow_html=True)

            if movie.get("director") or movie.get("cast"):
                st.markdown(
                    f"<p style='color: #9ca3af; font-size: 0.88rem; margin-top: 6px;'>"
                    f"Режиссер: {movie.get('director', 'н/д')} | В ролях: {movie.get('cast', 'н/д')}</p>",
                    unsafe_allow_html=True
                )

            if movie.get("description"):
                st.markdown(f"<p style='font-size: 0.92rem; line-height: 1.4;'>{movie.get('description')}</p>", unsafe_allow_html=True)

            if movie.get("explanation"):
                st.info(f"Обоснование: {movie.get('explanation')}")


def render_movie_grid(movies: list, show_score: str = None, cols_per_row: int = 3, key_prefix: str = ""):
    """Отрисовка карточек фильмов в виде сетки без эмодзи."""
    if not movies:
        st.info("Нет фильмов для отображения.")
        return

    for i in range(0, len(movies), cols_per_row):
        row_movies = movies[i:i + cols_per_row]
        cols = st.columns(cols_per_row)
        for col, movie in zip(cols, row_movies):
            with col:
                with st.container(border=True):
                    poster_path = resolve_poster_path(movie)
                    if poster_path:
                        st.image(poster_path, use_container_width=True)
                    else:
                        st.markdown(
                            """
                            <div style="background: #1f2937; height: 180px; border-radius: 6px;
                                        display: flex; align-items: center; justify-content: center; color: #9ca3af;">
                                Нет постера
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                    rank_prefix = f"#{movie.get('rank')} " if movie.get("rank") else ""
                    st.markdown(f"**{rank_prefix}{movie.get('title')}** ({movie.get('release_year', '—')})")

                    avg = movie.get("avg_rating", 0.0) or 0.0
                    cnt = movie.get("ratings_count", 0) or 0
                    st.markdown(f"Балл: **{avg:.2f}** ({cnt})")

                    if show_score == "weighted" and movie.get("weighted_score") is not None:
                        st.caption(f"Рейтинг: {movie.get('weighted_score'):.2f}")
                    elif show_score == "predicted" and movie.get("predicted_rating") is not None:
                        st.caption(f"Прогноз: {movie.get('predicted_rating'):.2f} / 5")
                    elif show_score == "similarity" and movie.get("similarity_score") is not None:
                        st.caption(f"Сходство: {movie.get('similarity_score')*100:.1f}%")

                    genres = movie.get("genres", "") or ""
                    short_genres = ", ".join([g.strip() for g in genres.split(",")][:2])
                    st.caption(f"Жанры: {short_genres}")

                    if movie.get("description"):
                        with st.expander("Описание"):
                            st.write(movie.get("description"))
                            if movie.get("explanation"):
                                st.info(movie.get("explanation"))
