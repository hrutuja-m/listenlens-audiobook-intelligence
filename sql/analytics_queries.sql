-- ============================================================
-- ListenLens: Core Analytics Queries
-- Audiobook Strategy Intelligence Platform
-- ============================================================


-- ============================================================
-- Query 1: Streaming time-cap friction
-- Business question:
-- Which listener segments frequently exceed a 15-hour
-- monthly streaming allowance?
-- ============================================================

WITH monthly_user_listening AS (
    SELECT
        ls.user_id,
        DATE_TRUNC('month', ls.session_date) AS listening_month,
        ROUND(SUM(ls.minutes_listened) / 60.0, 2) AS monthly_hours
    FROM listening_sessions AS ls
    GROUP BY
        ls.user_id,
        DATE_TRUNC('month', ls.session_date)
)

SELECT
    seg.segment_name,
    COUNT(*) AS user_months,
    ROUND(AVG(mul.monthly_hours), 2) AS avg_monthly_hours,
    ROUND(
        100.0 * SUM(
            CASE WHEN mul.monthly_hours > 15 THEN 1 ELSE 0 END
        ) / COUNT(*),
        2
    ) AS pct_user_months_over_15_hours
FROM monthly_user_listening AS mul
JOIN users AS u
    ON mul.user_id = u.user_id
JOIN listener_segments AS seg
    ON u.segment_id = seg.segment_id
GROUP BY seg.segment_name
ORDER BY pct_user_months_over_15_hours DESC;


-- ============================================================
-- Query 2: Ownership-model credit waste
-- Business question:
-- Which listener segments accumulate unused audiobook credits?
-- ============================================================

SELECT
    seg.segment_name,
    COUNT(*) AS subscribers,
    SUM(
        CASE WHEN s.unused_credits > 0 THEN 1 ELSE 0 END
    ) AS subscribers_with_unused_credits,
    ROUND(AVG(s.unused_credits), 2) AS avg_unused_credits,
    SUM(s.unused_credits) AS total_unused_credits,
    ROUND(
        100.0 * SUM(
            CASE WHEN s.unused_credits > 0 THEN 1 ELSE 0 END
        ) / COUNT(*),
        2
    ) AS credit_waste_rate_pct
FROM subscriptions AS s
JOIN users AS u
    ON s.user_id = u.user_id
JOIN listener_segments AS seg
    ON u.segment_id = seg.segment_id
JOIN platform_models AS pm
    ON s.model_id = pm.model_id
WHERE pm.access_type IN ('Ownership', 'Hybrid')
GROUP BY seg.segment_name
ORDER BY credit_waste_rate_pct DESC;


-- ============================================================
-- Query 3: Genre completion performance
-- Business question:
-- Which audiobook genres produce the strongest engagement?
-- ============================================================

SELECT
    b.genre,
    COUNT(*) AS listening_sessions,
    COUNT(DISTINCT ls.user_id) AS unique_listeners,
    COUNT(DISTINCT ls.book_id) AS books_streamed,
    ROUND(AVG(ls.completion_percentage), 2) AS avg_completion_pct,
    ROUND(AVG(ls.minutes_listened), 2) AS avg_session_minutes
FROM listening_sessions AS ls
JOIN books AS b
    ON ls.book_id = b.book_id
GROUP BY b.genre
ORDER BY avg_completion_pct DESC;


-- ============================================================
-- Query 4: Narrator impact
-- Business question:
-- Do higher-tier narrators improve ratings and completion?
-- ============================================================

WITH narrator_completion AS (
    SELECT
        n.narrator_id,
        n.performance_tier,
        COUNT(DISTINCT b.book_id) AS books_narrated,
        COUNT(ls.session_id) AS listening_sessions,
        AVG(ls.completion_percentage) AS avg_completion_pct
    FROM narrators AS n
    JOIN books AS b
        ON n.narrator_id = b.narrator_id
    LEFT JOIN listening_sessions AS ls
        ON b.book_id = ls.book_id
    GROUP BY
        n.narrator_id,
        n.performance_tier
),

narrator_ratings AS (
    SELECT
        n.narrator_id,
        AVG(r.rating_score) AS avg_listener_rating
    FROM narrators AS n
    JOIN books AS b
        ON n.narrator_id = b.narrator_id
    LEFT JOIN ratings AS r
        ON b.book_id = r.book_id
    GROUP BY n.narrator_id
)

SELECT
    nc.performance_tier,
    COUNT(*) AS narrators,
    SUM(nc.books_narrated) AS books_narrated,
    SUM(nc.listening_sessions) AS listening_sessions,
    ROUND(AVG(nc.avg_completion_pct), 2) AS avg_completion_pct,
    ROUND(AVG(nr.avg_listener_rating), 2) AS avg_listener_rating
FROM narrator_completion AS nc
LEFT JOIN narrator_ratings AS nr
    ON nc.narrator_id = nr.narrator_id
GROUP BY nc.performance_tier
ORDER BY avg_completion_pct DESC;


-- ============================================================
-- Query 5: Listener-segment business-model fit
-- Business question:
-- Which access model best fits each behavioral segment?
-- ============================================================

WITH listening_metrics AS (
    SELECT
        user_id,
        ROUND(SUM(minutes_listened) / 60.0, 2) AS total_hours,
        ROUND(AVG(completion_percentage), 2) AS avg_completion_pct
    FROM listening_sessions
    GROUP BY user_id
),

ownership_metrics AS (
    SELECT
        user_id,
        COUNT(*) AS books_owned,
        SUM(times_replayed) AS total_replays
    FROM book_ownership
    GROUP BY user_id
)

SELECT
    seg.segment_name,
    seg.preferred_access_model,
    COUNT(DISTINCT u.user_id) AS users,
    ROUND(AVG(COALESCE(lm.total_hours, 0)), 2) AS avg_total_hours,
    ROUND(AVG(COALESCE(lm.avg_completion_pct, 0)), 2)
        AS avg_completion_pct,
    ROUND(AVG(COALESCE(om.books_owned, 0)), 2) AS avg_books_owned,
    ROUND(AVG(COALESCE(om.total_replays, 0)), 2) AS avg_replays,
    ROUND(AVG(s.unused_credits), 2) AS avg_unused_credits
FROM users AS u
JOIN listener_segments AS seg
    ON u.segment_id = seg.segment_id
JOIN subscriptions AS s
    ON u.user_id = s.user_id
LEFT JOIN listening_metrics AS lm
    ON u.user_id = lm.user_id
LEFT JOIN ownership_metrics AS om
    ON u.user_id = om.user_id
GROUP BY
    seg.segment_name,
    seg.preferred_access_model
ORDER BY avg_total_hours DESC;


-- ============================================================
-- Query 6: Churn-risk indicators
-- Business question:
-- Which users should be prioritized for retention action?
-- ============================================================

WITH user_engagement AS (
    SELECT
        user_id,
        COUNT(*) AS session_count,
        SUM(minutes_listened) AS total_minutes,
        AVG(completion_percentage) AS avg_completion_pct,
        MAX(session_date) AS last_session_date
    FROM listening_sessions
    GROUP BY user_id
)

SELECT
    u.user_id,
    seg.segment_name,
    s.subscription_status,
    COALESCE(ue.session_count, 0) AS session_count,
    ROUND(COALESCE(ue.total_minutes, 0) / 60.0, 2)
        AS total_listening_hours,
    ROUND(COALESCE(ue.avg_completion_pct, 0), 2)
        AS avg_completion_pct,
    s.unused_credits,
    ue.last_session_date,

    (
        CASE
            WHEN s.subscription_status IN ('Cancelled', 'Paused')
                THEN 3
            ELSE 0
        END
        +
        CASE
            WHEN COALESCE(ue.session_count, 0) < 5
                THEN 2
            ELSE 0
        END
        +
        CASE
            WHEN COALESCE(ue.avg_completion_pct, 0) < 25
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
LEFT JOIN user_engagement AS ue
    ON u.user_id = ue.user_id
ORDER BY churn_risk_score DESC, total_listening_hours ASC
LIMIT 50;


-- ============================================================
-- Query 7: Recommendation conversion
-- Business question:
-- Which recommendation source creates the strongest funnel?
-- ============================================================

SELECT
    recommendation_source,
    COUNT(*) AS recommendations_shown,
    SUM(CASE WHEN clicked THEN 1 ELSE 0 END) AS clicks,
    SUM(
        CASE WHEN started_listening THEN 1 ELSE 0 END
    ) AS listening_starts,
    SUM(CASE WHEN completed THEN 1 ELSE 0 END) AS completions,

    ROUND(
        100.0 * SUM(CASE WHEN clicked THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS click_through_rate_pct,

    ROUND(
        100.0 * SUM(
            CASE WHEN started_listening THEN 1 ELSE 0 END
        ) / COUNT(*),
        2
    ) AS start_rate_pct,

    ROUND(
        100.0 * SUM(CASE WHEN completed THEN 1 ELSE 0 END)
        / COUNT(*),
        2
    ) AS completion_conversion_pct

FROM recommendations
GROUP BY recommendation_source
ORDER BY completion_conversion_pct DESC;


-- ============================================================
-- Query 8: Long-book completion friction
-- Business question:
-- Do longer audiobooks reduce listener completion?
-- ============================================================

WITH duration_groups AS (
    SELECT
        book_id,
        duration_minutes,
        CASE
            WHEN duration_minutes < 360 THEN 'Short: under 6 hours'
            WHEN duration_minutes < 720 THEN 'Medium: 6-12 hours'
            WHEN duration_minutes < 1_080 THEN 'Long: 12-18 hours'
            ELSE 'Very Long: 18+ hours'
        END AS duration_bucket
    FROM books
)

SELECT
    dg.duration_bucket,
    COUNT(*) AS listening_sessions,
    COUNT(DISTINCT ls.user_id) AS unique_listeners,
    COUNT(DISTINCT ls.book_id) AS books_streamed,
    ROUND(AVG(dg.duration_minutes) / 60.0, 2)
        AS avg_book_duration_hours,
    ROUND(AVG(ls.minutes_listened), 2)
        AS avg_session_minutes,
    ROUND(AVG(ls.completion_percentage), 2)
        AS avg_completion_pct
FROM listening_sessions AS ls
JOIN duration_groups AS dg
    ON ls.book_id = dg.book_id
GROUP BY dg.duration_bucket
ORDER BY avg_book_duration_hours;