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
    st.caption(
        "Compare streaming, ownership, and hybrid access models "
        "across listener segments."
    )

    subscription_summary = run_query(
        """
        SELECT
            pm.access_type,
            COUNT(*) AS subscribers,
            ROUND(AVG(s.monthly_price), 2) AS avg_monthly_price,
            ROUND(AVG(s.unused_credits), 2) AS avg_unused_credits
        FROM subscriptions AS s
        JOIN platform_models AS pm
            ON s.model_id = pm.model_id
        GROUP BY pm.access_type
        ORDER BY subscribers DESC
        """
    )

    col1, col2, col3 = st.columns(3)

    for column, row in zip(
        [col1, col2, col3],
        subscription_summary.itertuples(),
    ):
        column.metric(
            f"{row.access_type} Subscribers",
            f"{int(row.subscribers):,}",
        )

    st.divider()

    chart_col1, chart_col2 = st.columns(2)

    model_distribution = px.bar(
        subscription_summary,
        x="access_type",
        y="subscribers",
        title="Subscribers by Access Model",
        labels={
            "access_type": "Access Model",
            "subscribers": "Subscribers",
        },
    )

    chart_col1.plotly_chart(
        model_distribution,
        use_container_width=True,
    )

    credit_waste = run_query(
        """
        SELECT
            seg.segment_name,
            ROUND(AVG(s.unused_credits), 2)
                AS avg_unused_credits,
            SUM(s.unused_credits) AS total_unused_credits
        FROM subscriptions AS s
        JOIN users AS u
            ON s.user_id = u.user_id
        JOIN listener_segments AS seg
            ON u.segment_id = seg.segment_id
        JOIN platform_models AS pm
            ON s.model_id = pm.model_id
        WHERE pm.access_type IN ('Ownership', 'Hybrid')
        GROUP BY seg.segment_name
        ORDER BY avg_unused_credits DESC
        """
    )

    credit_figure = px.bar(
        credit_waste,
        x="segment_name",
        y="avg_unused_credits",
        title="Average Unused Credits by Segment",
        labels={
            "segment_name": "Listener Segment",
            "avg_unused_credits": "Average Unused Credits",
        },
    )

    chart_col2.plotly_chart(
        credit_figure,
        use_container_width=True,
    )

    st.divider()

    cap_friction = run_query(
        """
        WITH monthly_listening AS (
            SELECT
                user_id,
                DATE_TRUNC('month', session_date)
                    AS listening_month,
                SUM(minutes_listened) / 60.0 AS monthly_hours
            FROM listening_sessions
            GROUP BY
                user_id,
                DATE_TRUNC('month', session_date)
        )

        SELECT
            seg.segment_name,
            ROUND(AVG(ml.monthly_hours), 2)
                AS avg_monthly_hours,
            ROUND(
                100.0 * SUM(
                    CASE
                        WHEN ml.monthly_hours > 15 THEN 1
                        ELSE 0
                    END
                ) / COUNT(*),
                2
            ) AS pct_over_15_hour_cap
        FROM monthly_listening AS ml
        JOIN users AS u
            ON ml.user_id = u.user_id
        JOIN listener_segments AS seg
            ON u.segment_id = seg.segment_id
        GROUP BY seg.segment_name
        ORDER BY pct_over_15_hour_cap DESC
        """
    )

    cap_figure = px.bar(
        cap_friction,
        x="segment_name",
        y="pct_over_15_hour_cap",
        title="Streaming 15-Hour Cap Friction",
        labels={
            "segment_name": "Listener Segment",
            "pct_over_15_hour_cap": "User-Months Above Cap (%)",
        },
    )

    st.plotly_chart(
        cap_figure,
        use_container_width=True,
    )

    st.subheader("Model-fit summary")
    st.dataframe(
        cap_friction,
        use_container_width=True,
        hide_index=True,
    )


def render_listener_behavior() -> None:
    st.title("Listener Behavior")
    st.caption(
        "Explore listening activity, device usage, timing patterns, "
        "and churn-risk signals."
    )

    behavior_metrics = run_query(
        """
        SELECT
            COUNT(DISTINCT user_id) AS listeners,
            ROUND(AVG(minutes_listened), 2)
                AS avg_session_minutes,
            ROUND(AVG(completion_percentage), 2)
                AS avg_completion_pct,
            COUNT(
                CASE
                    WHEN session_day_type = 'Weekend'
                    THEN 1
                END
            ) AS weekend_sessions
        FROM listening_sessions
        """
    )

    row = behavior_metrics.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Listeners",
        f"{int(row['listeners']):,}",
    )

    col2.metric(
        "Avg Session",
        f"{row['avg_session_minutes']:.1f} min",
    )

    col3.metric(
        "Avg Completion",
        f"{row['avg_completion_pct']:.1f}%",
    )

    col4.metric(
        "Weekend Sessions",
        f"{int(row['weekend_sessions']):,}",
    )

    st.divider()

    monthly_activity = run_query(
        """
        SELECT
            DATE_TRUNC('month', session_date)
                AS listening_month,
            COUNT(*) AS sessions,
            ROUND(SUM(minutes_listened) / 60.0, 2)
                AS listening_hours
        FROM listening_sessions
        GROUP BY DATE_TRUNC('month', session_date)
        ORDER BY listening_month
        """
    )

    monthly_figure = px.line(
        monthly_activity,
        x="listening_month",
        y="listening_hours",
        markers=True,
        title="Monthly Listening Hours",
        labels={
            "listening_month": "Month",
            "listening_hours": "Listening Hours",
        },
    )

    st.plotly_chart(
        monthly_figure,
        use_container_width=True,
    )

    chart_col1, chart_col2 = st.columns(2)

    device_usage = run_query(
        """
        SELECT
            device_type,
            COUNT(*) AS sessions
        FROM listening_sessions
        GROUP BY device_type
        ORDER BY sessions DESC
        """
    )

    device_figure = px.bar(
        device_usage,
        x="device_type",
        y="sessions",
        title="Listening Sessions by Device",
        labels={
            "device_type": "Device",
            "sessions": "Sessions",
        },
    )

    chart_col1.plotly_chart(
        device_figure,
        use_container_width=True,
    )

    day_type = run_query(
        """
        SELECT
            session_day_type,
            COUNT(*) AS sessions,
            ROUND(AVG(minutes_listened), 2)
                AS avg_session_minutes
        FROM listening_sessions
        GROUP BY session_day_type
        ORDER BY sessions DESC
        """
    )

    day_figure = px.bar(
        day_type,
        x="session_day_type",
        y="sessions",
        title="Weekday vs Weekend Activity",
        labels={
            "session_day_type": "Day Type",
            "sessions": "Sessions",
        },
    )

    chart_col2.plotly_chart(
        day_figure,
        use_container_width=True,
    )

    st.divider()
    st.subheader("Highest-priority churn-risk accounts")

    churn_risk = run_query(
        """
        WITH engagement AS (
            SELECT
                user_id,
                COUNT(*) AS session_count,
                ROUND(SUM(minutes_listened) / 60.0, 2)
                    AS total_hours,
                ROUND(AVG(completion_percentage), 2)
                    AS avg_completion_pct
            FROM listening_sessions
            GROUP BY user_id
        )

        SELECT
            u.user_id,
            seg.segment_name,
            s.subscription_status,
            COALESCE(e.session_count, 0) AS session_count,
            COALESCE(e.total_hours, 0) AS total_hours,
            COALESCE(e.avg_completion_pct, 0)
                AS avg_completion_pct,
            s.unused_credits,
            (
                CASE
                    WHEN s.subscription_status
                        IN ('Cancelled', 'Paused')
                    THEN 3
                    ELSE 0
                END
                +
                CASE
                    WHEN COALESCE(e.session_count, 0) < 5
                    THEN 2
                    ELSE 0
                END
                +
                CASE
                    WHEN COALESCE(e.avg_completion_pct, 0) < 25
                    THEN 2
                    ELSE 0
                END
                +
                CASE
                    WHEN s.unused_credits >= 2
                    THEN 1
                    ELSE 0
                END
                +
                CASE
                    WHEN u.is_active = FALSE
                    THEN 3
                    ELSE 0
                END
            ) AS churn_risk_score
        FROM users AS u
        JOIN listener_segments AS seg
            ON u.segment_id = seg.segment_id
        JOIN subscriptions AS s
            ON u.user_id = s.user_id
        LEFT JOIN engagement AS e
            ON u.user_id = e.user_id
        ORDER BY
            churn_risk_score DESC,
            total_hours ASC
        LIMIT 20
        """
    )

    st.dataframe(
        churn_risk,
        use_container_width=True,
        hide_index=True,
    )


def render_content_performance() -> None:
    st.title("Content Performance")
    st.caption(
        "Evaluate genre engagement, narrator performance, "
        "ratings, and audiobook-duration friction."
    )

    content_metrics = run_query(
        """
        SELECT
            COUNT(DISTINCT b.book_id) AS total_books,
            COUNT(DISTINCT b.genre) AS genres,
            COUNT(DISTINCT b.narrator_id) AS narrators,
            ROUND(AVG(r.rating_score), 2) AS avg_rating
        FROM books AS b
        LEFT JOIN ratings AS r
            ON b.book_id = r.book_id
        """
    )

    row = content_metrics.iloc[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Books", f"{int(row['total_books']):,}")
    col2.metric("Genres", f"{int(row['genres']):,}")
    col3.metric("Narrators", f"{int(row['narrators']):,}")
    col4.metric("Avg Rating", f"{row['avg_rating']:.2f}/5")

    st.divider()

    chart_col1, chart_col2 = st.columns(2)

    genre_performance = run_query(
        """
        SELECT
            b.genre,
            COUNT(*) AS sessions,
            ROUND(AVG(ls.completion_percentage), 2)
                AS avg_completion_pct
        FROM listening_sessions AS ls
        JOIN books AS b
            ON ls.book_id = b.book_id
        GROUP BY b.genre
        ORDER BY avg_completion_pct DESC
        """
    )

    genre_figure = px.bar(
        genre_performance,
        x="genre",
        y="avg_completion_pct",
        title="Average Completion by Genre",
        labels={
            "genre": "Genre",
            "avg_completion_pct": "Average Completion (%)",
        },
    )

    chart_col1.plotly_chart(
        genre_figure,
        use_container_width=True,
    )

    narrator_performance = run_query(
        """
        SELECT
            n.performance_tier,
            COUNT(DISTINCT n.narrator_id) AS narrators,
            ROUND(AVG(ls.completion_percentage), 2)
                AS avg_completion_pct,
            ROUND(AVG(r.rating_score), 2)
                AS avg_rating
        FROM narrators AS n
        JOIN books AS b
            ON n.narrator_id = b.narrator_id
        LEFT JOIN listening_sessions AS ls
            ON b.book_id = ls.book_id
        LEFT JOIN ratings AS r
            ON b.book_id = r.book_id
        GROUP BY n.performance_tier
        ORDER BY avg_completion_pct DESC
        """
    )

    narrator_figure = px.bar(
        narrator_performance,
        x="performance_tier",
        y="avg_completion_pct",
        title="Completion by Narrator Tier",
        labels={
            "performance_tier": "Narrator Tier",
            "avg_completion_pct": "Average Completion (%)",
        },
    )

    chart_col2.plotly_chart(
        narrator_figure,
        use_container_width=True,
    )

    st.divider()

    duration_performance = run_query(
        """
        WITH duration_groups AS (
            SELECT
                book_id,
                CASE
                    WHEN duration_minutes < 360
                        THEN 'Under 6 hours'
                    WHEN duration_minutes < 720
                        THEN '6-12 hours'
                    WHEN duration_minutes < 1080
                        THEN '12-18 hours'
                    ELSE '18+ hours'
                END AS duration_bucket,
                CASE
                    WHEN duration_minutes < 360 THEN 1
                    WHEN duration_minutes < 720 THEN 2
                    WHEN duration_minutes < 1080 THEN 3
                    ELSE 4
                END AS bucket_order
            FROM books
        )

        SELECT
            dg.duration_bucket,
            dg.bucket_order,
            COUNT(*) AS sessions,
            ROUND(AVG(ls.completion_percentage), 2)
                AS avg_completion_pct
        FROM listening_sessions AS ls
        JOIN duration_groups AS dg
            ON ls.book_id = dg.book_id
        GROUP BY
            dg.duration_bucket,
            dg.bucket_order
        ORDER BY dg.bucket_order
        """
    )

    duration_figure = px.line(
        duration_performance,
        x="duration_bucket",
        y="avg_completion_pct",
        markers=True,
        title="Completion Friction by Audiobook Duration",
        labels={
            "duration_bucket": "Audiobook Duration",
            "avg_completion_pct": "Average Completion (%)",
        },
    )

    st.plotly_chart(
        duration_figure,
        use_container_width=True,
    )

    rating_distribution = run_query(
        """
        SELECT
            rating_score,
            COUNT(*) AS ratings
        FROM ratings
        GROUP BY rating_score
        ORDER BY rating_score
        """
    )

    rating_figure = px.bar(
        rating_distribution,
        x="rating_score",
        y="ratings",
        title="Listener Rating Distribution",
        labels={
            "rating_score": "Rating Score",
            "ratings": "Number of Ratings",
        },
    )

    st.plotly_chart(
        rating_figure,
        use_container_width=True,
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