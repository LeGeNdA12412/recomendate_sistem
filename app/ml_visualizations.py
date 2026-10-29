import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


def render_dataset_overview_tab(summary: dict):
    """Сводка данных и столбчатая диаграмма разреженности матрицы."""
    st.markdown("### Сводка данных и структура матрицы взаимодействий")

    total_users = summary.get("total_users", 0)
    total_movies = summary.get("total_movies", 0)
    total_ratings = summary.get("total_ratings", 0)
    sparsity_pct = float(summary.get("sparsity_pct", 0.0))
    density_pct = float(summary.get("density_pct", round(100.0 - sparsity_pct, 2)))
    mean_rating = summary.get("mean_rating", 0.0)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Пользователей", total_users)
    with c2:
        st.metric("Фильмов", total_movies)
    with c3:
        st.metric("Оценок", total_ratings)
    with c4:
        st.metric("Средний балл", f"{mean_rating:.2f} / 5.0")

    col_chart, col_info = st.columns([1.5, 2.5])

    with col_chart:
        df_matrix = pd.DataFrame([
            {"Параметр": "Разреженность", "Процент": sparsity_pct, "Цвет": "#ef4444"},
            {"Параметр": "Заполненность", "Процент": density_pct, "Цвет": "#10b981"}
        ])

        fig_matrix = go.Figure(go.Bar(
            x=df_matrix["Параметр"],
            y=df_matrix["Процент"],
            text=[f"{v:.2f}%" for v in df_matrix["Процент"]],
            textposition="auto",
            marker_color=df_matrix["Цвет"],
            width=0.45
        ))
        fig_matrix.update_layout(
            title="Заполненность матрицы взаимодействий (%)",
            yaxis=dict(range=[0, 105], title="Процент"),
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_matrix, use_container_width=True)

    with col_info:
        st.markdown(f"""
        <div style="background-color: #1f2937; border-radius: 8px; padding: 18px; margin-top: 20px;">
            <h4 style="margin-top: 0; color: #60a5fa;">Параметры матрицы взаимодействий</h4>
            <p><b>Размерность матрицы:</b> <code>{summary.get('matrix_dimensions', '0x0')}</code></p>
            <p><b>Возможных взаимодействий (Users × Movies):</b> {summary.get('possible_ratings', 0):,}</p>
            <p><b>Фактических оценок в базе:</b> {total_ratings:,}</p>
            <p><b>Коэффициент разреженности:</b> {sparsity_pct:.2f}%</p>
            <p style="color: #9ca3af; font-size: 0.9rem; margin-bottom: 0;">
                Разреженность матрицы составляет {sparsity_pct:.1f}%. Это означает, что заполнено только {density_pct:.2f}% ячеек,
                поэтому для качественных рекомендаций применяются гибридные алгоритмы на основе SVD и TF-IDF.
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_distribution_charts(rating_dist: list, genre_dist: list):
    """Столбчатые диаграммы распределения оценок и каталога по жанрам."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Распределение выставленных оценок")
        if rating_dist:
            df_r = pd.DataFrame(rating_dist)
            total_r = df_r["count"].sum()
            df_r["pct"] = (df_r["count"] / total_r * 100).round(1)

            fig_r = go.Figure(go.Bar(
                x=[str(x) for x in df_r["rating"]],
                y=df_r["count"],
                text=[f"{cnt} ({pct}%)" for cnt, pct in zip(df_r["count"], df_r["pct"])],
                textposition="outside",
                marker_color="#3b82f6"
            ))

            avg_val = (df_r["rating"] * df_r["count"]).sum() / total_r
            fig_r.add_vline(
                x=str(round(avg_val * 2) / 2),
                line_dash="dash",
                line_color="#f59e0b",
                annotation_text=f"Среднее: {avg_val:.2f}",
                annotation_position="top left"
            )

            fig_r.update_layout(
                xaxis_title="Балл рейтинга",
                yaxis_title="Количество оценок",
                height=350,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.info("Нет данных по распределению оценок.")

    with col2:
        st.markdown("#### Количество фильмов по жанрам")
        if genre_dist:
            df_g = pd.DataFrame(genre_dist).sort_values("count", ascending=True)

            fig_g = go.Figure(go.Bar(
                x=df_g["count"],
                y=df_g["genre"],
                orientation="h",
                text=df_g["count"],
                textposition="auto",
                marker_color="#10b981"
            ))

            fig_g.update_layout(
                xaxis_title="Количество фильмов",
                yaxis_title="Жанр",
                height=350,
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig_g, use_container_width=True)
        else:
            st.info("Нет данных по жанрам.")


def render_model_evaluation_chart(eval_data: dict):
    """Столбчатые диаграммы сравнения моделей ML: ошибки и точность."""
    st.markdown("### Сравнение моделей машинного обучения")

    models_data = eval_data.get("models", {})
    if not models_data:
        st.info("Недостаточно данных для оценки моделей.")
        return

    rows = []
    for model_name, metrics in models_data.items():
        rows.append({
            "Модель": model_name,
            "RMSE": metrics.get("rmse", 0.0),
            "MAE": metrics.get("mae", 0.0),
            "Precision": metrics.get("precision", 0.0),
            "Recall": metrics.get("recall", 0.0),
        })
    df_eval = pd.DataFrame(rows)

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Ошибки прогноза: RMSE и MAE (меньше — лучше)")
        fig_err = go.Figure()
        fig_err.add_trace(go.Bar(
            x=df_eval["Модель"],
            y=df_eval["RMSE"],
            name="RMSE",
            text=df_eval["RMSE"],
            textposition="auto",
            marker_color="#ef4444"
        ))
        fig_err.add_trace(go.Bar(
            x=df_eval["Модель"],
            y=df_eval["MAE"],
            name="MAE",
            text=df_eval["MAE"],
            textposition="auto",
            marker_color="#f59e0b"
        ))
        fig_err.update_layout(
            barmode="group",
            yaxis_title="Величина ошибки",
            height=340,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=1.15)
        )
        st.plotly_chart(fig_err, use_container_width=True)

    with c2:
        st.markdown("##### Метрики качества: Precision и Recall (больше — лучше)")
        fig_acc = go.Figure()
        fig_acc.add_trace(go.Bar(
            x=df_eval["Модель"],
            y=df_eval["Precision"],
            name="Precision",
            text=df_eval["Precision"],
            textposition="auto",
            marker_color="#3b82f6"
        ))
        fig_acc.add_trace(go.Bar(
            x=df_eval["Модель"],
            y=df_eval["Recall"],
            name="Recall",
            text=df_eval["Recall"],
            textposition="auto",
            marker_color="#8b5cf6"
        ))
        fig_acc.update_layout(
            barmode="group",
            yaxis_title="Коэффициент качества",
            height=340,
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", y=1.15)
        )
        st.plotly_chart(fig_acc, use_container_width=True)

    st.markdown("##### Сводная таблица численных метрик")
    st.dataframe(df_eval, use_container_width=True)


def render_svd_scree_chart(scree_data: dict):
    """Столбчатая диаграмма каменистой осыпи SVD (Scree Plot)."""
    st.markdown("### Каменистая осыпь SVD (Scree Plot)")
    st.caption("Доля информации (дисперсии), объясняемая каждым скрытым фактором матрицы взаимодействий.")

    components = scree_data.get("components", [])
    exp_var = scree_data.get("explained_variance_pct", [])
    cum_var = scree_data.get("cumulative_variance_pct", [])

    if not components or not exp_var:
        st.info("Недостаточно данных для Scree Plot.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("##### Доля дисперсии по факторам (%)")
        fig_single = go.Figure(go.Bar(
            x=components,
            y=exp_var,
            text=[f"{v:.1f}%" for v in exp_var],
            textposition="auto",
            marker_color="#3b82f6"
        ))
        fig_single.update_layout(
            yaxis_title="Дисперсия фактора (%)",
            height=320,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_single, use_container_width=True)

    with c2:
        st.markdown("##### Накопленная дисперсия (%)")
        fig_cum = go.Figure(go.Bar(
            x=components,
            y=cum_var,
            text=[f"{v:.1f}%" for v in cum_var],
            textposition="auto",
            marker_color="#10b981"
        ))
        fig_cum.add_hline(
            y=80.0,
            line_dash="dash",
            line_color="#f59e0b",
            annotation_text="Порог 80%",
            annotation_position="top left"
        )
        fig_cum.update_layout(
            yaxis=dict(range=[0, 105], title="Накопленный %"),
            height=320,
            margin=dict(l=20, r=20, t=20, b=20)
        )
        st.plotly_chart(fig_cum, use_container_width=True)


def render_pca_projection(pca_data: list):
    """Столбчатая диаграмма распределения средней проекции компонент по жанрам."""
    st.markdown("### Анализ главных компонент (PCA) по жанрам")
    st.caption("Средняя проекция признаков фильмов на первую главную компоненту (PC1) по жанрам.")

    if not pca_data:
        st.info("Нет данных для отображения PCA.")
        return

    df_pca = pd.DataFrame(pca_data)
    df_grouped = df_pca.groupby("genre").agg(
        avg_pc1=("pc1", "mean"),
        count=("movie_id", "count")
    ).reset_index().sort_values("avg_pc1", ascending=False)

    fig_pca = go.Figure(go.Bar(
        x=df_grouped["genre"],
        y=df_grouped["avg_pc1"],
        text=[f"{val:.2f} (N={cnt})" for val, cnt in zip(df_grouped["avg_pc1"], df_grouped["count"])],
        textposition="outside",
        marker_color="#6366f1"
    ))
    fig_pca.update_layout(
        xaxis_title="Жанр",
        yaxis_title="Среднее значение PC1",
        height=350,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_pca, use_container_width=True)


def render_similarity_heatmap(sim_data: dict):
    """Столбчатая диаграмма наиболее похожих пар фильмов по косинусному сходству."""
    st.markdown("### Топ пар фильмов с наибольшим сходством")
    st.caption("Пары фильмов из выборки с наивысшим косинусным сходством по описанию и создателям.")

    titles = sim_data.get("titles", [])
    matrix = sim_data.get("matrix", [])

    if not titles or not matrix:
        st.info("Нет данных для анализа сходства.")
        return

    pairs = []
    n = len(titles)
    for i in range(n):
        for j in range(i + 1, n):
            pairs.append({
                "Пара фильмов": f"{titles[i]} / {titles[j]}",
                "Сходство": float(matrix[i][j])
            })

    df_pairs = pd.DataFrame(pairs).sort_values("Сходство", ascending=False).head(8)

    fig_sim = go.Figure(go.Bar(
        x=df_pairs["Сходство"],
        y=df_pairs["Пара фильмов"],
        orientation="h",
        text=[f"{v:.2f}" for v in df_pairs["Сходство"]],
        textposition="auto",
        marker_color="#06b6d4"
    ))
    fig_sim.update_layout(
        xaxis=dict(range=[0, 1.05], title="Косинусное сходство (от 0 до 1)"),
        yaxis=dict(autorange="reversed"),
        height=350,
        margin=dict(l=20, r=20, t=20, b=20)
    )
    st.plotly_chart(fig_sim, use_container_width=True)
