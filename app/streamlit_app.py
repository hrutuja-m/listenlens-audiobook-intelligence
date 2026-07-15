from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "listenlens.duckdb"


st.set_page_config(
    page_title="ListenLens",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded",
)


if not DATABASE_PATH.exists():
    st.error(
        "ListenLens database not found. "
        "Run `python src/generate_data.py` and "
        "`python src/load_database.py` first."
    )
    st.stop()


@st.cache_data
def run_query(query: str) -> pd.DataFrame:
    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        return connection.execute(query).fetchdf()
    finally:
        connection.close()


def render_executive_overview() -> None:
    st.title("ListenLens")
    st.subheader("Executive Overview")
    st.caption(
        "Audiobook listener behavior, engagement, "
        "subscription health, and content performance."
    )

    metrics = run_query(
        """
        SELECT
            COUNT(DISTINCT u.user_id) AS total_users,
            COUNT(DISTINCT CASE
                WHEN u.is_active THEN u.user_id
            END) AS active_users,
            COUNT(ls.session_id) AS total_sessions,
            ROUND(
                SUM(ls.minutes_listened) / 60.0,
                2
            ) AS total_listening_hours,
            ROUND(
                AVG(ls.completion_percentage),
                2
            ) AS avg_completion_pct
        FROM users AS u
        LEFT JOIN listening_sessions AS ls
            ON u.user_id = ls.user_id
        """
    )

    row = metrics.iloc[0]

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Total Users",
        f"{int(row['total_users']):,}",
    )

    col2.metric(
    "Active Accounts",
    f"{int(row['active_users']):,}",
  )

    col3.metric(
        "Listening Sessions",
        f"{int(row['total_sessions']):,}",
    )

    col4.metric(
        "Listening Hours",
        f"{row['total_listening_hours']:,.0f}",
    )

    col5.metric(
        "Avg Completion",
        f"{row['avg_completion_pct']:.1f}%",
    )

    st.divider()

    segment_data = run_query(
        """
        SELECT
            ls.segment_name,
            COUNT(u.user_id) AS users
        FROM users AS u
        JOIN listener_segments AS ls
            ON u.segment_id = ls.segment_id
        GROUP BY ls.segment_name
        ORDER BY users DESC
        """
    )

    figure = px.bar(
        segment_data,
        x="segment_name",
        y="users",
        title="Users by Listener Segment",
        labels={
            "segment_name": "Listener Segment",
            "users": "Users",
        },
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )


def render_business_model_fit() -> None:
    st.title("Business Model Fit")
    st.info(
        "Streaming, ownership, and hybrid model "
        "analysis will appear here."
    )


def render_listener_behavior() -> None:
    st.title("Listener Behavior")
    st.info(
        "Listener activity, device usage, and churn-risk "
        "analysis will appear here."
    )


def render_content_performance() -> None:
    st.title("Content Performance")
    st.info(
        "Genre, narrator, rating, and duration insights "
        "will appear here."
    )


def main() -> None:
    st.sidebar.title("ListenLens")

    page = st.sidebar.radio(
        "Dashboard section",
        [
            "Executive Overview",
            "Business Model Fit",
            "Listener Behavior",
            "Content Performance",
        ],
    )

    if page == "Executive Overview":
        render_executive_overview()

    elif page == "Business Model Fit":
        render_business_model_fit()

    elif page == "Listener Behavior":
        render_listener_behavior()

    else:
        render_content_performance()


if __name__ == "__main__":
    main()