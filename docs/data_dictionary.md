# ListenLens Data Dictionary

This document defines the core tables and fields used in the ListenLens audiobook analytics platform.

## 1. narrators

Stores narrator profile and performance information.

| Column | Type | Description |
|---|---|---|
| narrator_id | INTEGER | Unique narrator identifier |
| narrator_name | VARCHAR | Narrator full name |
| gender | VARCHAR | Narrator gender |
| experience_years | INTEGER | Number of years of narration experience |
| performance_tier | VARCHAR | Performance category such as Standard, Premium, or Elite |
| average_rating | DECIMAL(3,2) | Average listener rating for the narrator |

## 2. books

Stores audiobook metadata.

| Column | Type | Description |
|---|---|---|
| book_id | INTEGER | Unique audiobook identifier |
| title | VARCHAR | Audiobook title |
| author_name | VARCHAR | Author name |
| narrator_id | INTEGER | Foreign key referencing narrators |
| genre | VARCHAR | Audiobook genre |
| duration_minutes | INTEGER | Total audiobook duration in minutes |
| release_year | INTEGER | Publication or audiobook release year |
| language | VARCHAR | Audiobook language |
| average_rating | DECIMAL(3,2) | Average audiobook rating |

## 3. listener_segments

Defines behavioral listener groups.

| Column | Type | Description |
|---|---|---|
| segment_id | INTEGER | Unique segment identifier |
| segment_name | VARCHAR | Segment name such as Casual, Power, or Collector |
| segment_description | VARCHAR | Description of listener behavior |
| monthly_listening_hours | DECIMAL(6,2) | Typical monthly listening duration |
| preferred_access_model | VARCHAR | Streaming, Ownership, or Hybrid |
| churn_risk_level | VARCHAR | Low, Medium, or High churn risk |

## 4. users

Stores listener profile information.

| Column | Type | Description |
|---|---|---|
| user_id | INTEGER | Unique user identifier |
| signup_date | DATE | Account registration date |
| country | VARCHAR | User country |
| age_group | VARCHAR | User age category |
| device_type | VARCHAR | Primary listening device |
| preferred_genre | VARCHAR | User's preferred audiobook genre |
| segment_id | INTEGER | Foreign key referencing listener_segments |
| is_active | BOOLEAN | Whether the account is currently active |

## 5. platform_models

Defines audiobook access and subscription models.

| Column | Type | Description |
|---|---|---|
| model_id | INTEGER | Unique platform model identifier |
| model_name | VARCHAR | Model name |
| access_type | VARCHAR | Streaming, Ownership, or Hybrid |
| monthly_price | DECIMAL(8,2) | Monthly subscription price |
| monthly_hour_limit | INTEGER | Included monthly listening hours |
| monthly_credit_allowance | INTEGER | Monthly audiobook credits |
| ownership_included | BOOLEAN | Whether purchased books remain owned |

## 6. subscriptions

Stores user subscription records.

| Column | Type | Description |
|---|---|---|
| subscription_id | INTEGER | Unique subscription identifier |
| user_id | INTEGER | Foreign key referencing users |
| model_id | INTEGER | Foreign key referencing platform_models |
| plan_name | VARCHAR | Subscription plan name |
| monthly_price | DECIMAL(8,2) | User's monthly subscription cost |
| subscription_status | VARCHAR | Active, Cancelled, Paused, or Trial |
| start_date | DATE | Subscription start date |
| cancellation_date | DATE | Subscription cancellation date |
| unused_credits | INTEGER | Number of unused credits |

## 7. book_ownership

Tracks audiobook purchases and ownership behavior.

| Column | Type | Description |
|---|---|---|
| ownership_id | INTEGER | Unique ownership record identifier |
| user_id | INTEGER | Foreign key referencing users |
| book_id | INTEGER | Foreign key referencing books |
| acquisition_date | DATE | Date the audiobook was acquired |
| acquisition_method | VARCHAR | Credit, Direct Purchase, Gift, or Promotion |
| credits_used | INTEGER | Number of credits used |
| purchase_price | DECIMAL(8,2) | Direct purchase price |
| times_replayed | INTEGER | Number of times the audiobook was replayed |

## 8. listening_sessions

Stores session-level audiobook engagement.

| Column | Type | Description |
|---|---|---|
| session_id | INTEGER | Unique listening session identifier |
| user_id | INTEGER | Foreign key referencing users |
| book_id | INTEGER | Foreign key referencing books |
| session_date | DATE | Date of listening activity |
| minutes_listened | INTEGER | Minutes listened during the session |
| chapter_number | INTEGER | Chapter reached during the session |
| completion_percentage | DECIMAL(5,2) | Percentage of the audiobook completed |
| device_type | VARCHAR | Device used during the session |
| session_day_type | VARCHAR | Weekday or Weekend |

## 9. ratings

Stores audiobook rating and sentiment information.

| Column | Type | Description |
|---|---|---|
| rating_id | INTEGER | Unique rating identifier |
| user_id | INTEGER | Foreign key referencing users |
| book_id | INTEGER | Foreign key referencing books |
| rating_score | INTEGER | Rating from 1 to 5 |
| review_sentiment | VARCHAR | Positive, Neutral, or Negative |
| rating_date | DATE | Date the rating was submitted |

## 10. recommendations

Tracks recommendation performance.

| Column | Type | Description |
|---|---|---|
| recommendation_id | INTEGER | Unique recommendation identifier |
| user_id | INTEGER | Foreign key referencing users |
| book_id | INTEGER | Foreign key referencing books |
| recommendation_source | VARCHAR | Source such as Homepage, Genre, Trending, or Personalized |
| recommendation_date | DATE | Date the recommendation was shown |
| clicked | BOOLEAN | Whether the recommendation was clicked |
| started_listening | BOOLEAN | Whether the audiobook was started |
| completed | BOOLEAN | Whether the audiobook was completed |