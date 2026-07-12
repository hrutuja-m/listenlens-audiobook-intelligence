from __future__ import annotations

import random
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker


SEED = 42
OUTPUT_DIR = Path("data/synthetic")

NUM_USERS = 1_000
NUM_BOOKS = 300
NUM_NARRATORS = 50
NUM_LISTENING_SESSIONS = 10_000
NUM_RATINGS = 2_000
NUM_RECOMMENDATIONS = 3_000

random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)


GENRES = [
    "Fantasy",
    "Mystery",
    "Romance",
    "Science Fiction",
    "Biography",
    "Self Help",
    "History",
    "Business",
    "Thriller",
    "Young Adult",
]

COUNTRIES = [
    "United States",
    "Canada",
    "United Kingdom",
    "India",
    "Australia",
]

AGE_GROUPS = ["18-24", "25-34", "35-44", "45-54", "55+"]

DEVICES = ["Mobile", "Tablet", "Desktop", "Smart Speaker", "Car"]

SEGMENTS = [
    {
        "segment_id": 1,
        "segment_name": "Casual",
        "segment_description": "Listens occasionally and prefers low commitment access.",
        "monthly_listening_hours": 6.0,
        "preferred_access_model": "Streaming",
        "churn_risk_level": "Medium",
    },
    {
        "segment_id": 2,
        "segment_name": "Power",
        "segment_description": "Listens heavily and frequently exceeds streaming limits.",
        "monthly_listening_hours": 28.0,
        "preferred_access_model": "Hybrid",
        "churn_risk_level": "Low",
    },
    {
        "segment_id": 3,
        "segment_name": "Collector",
        "segment_description": "Prefers permanent ownership of selected audiobooks.",
        "monthly_listening_hours": 15.0,
        "preferred_access_model": "Ownership",
        "churn_risk_level": "Low",
    },
    {
        "segment_id": 4,
        "segment_name": "Rereader",
        "segment_description": "Frequently replays previously completed audiobooks.",
        "monthly_listening_hours": 18.0,
        "preferred_access_model": "Ownership",
        "churn_risk_level": "Low",
    },
    {
        "segment_id": 5,
        "segment_name": "Trial",
        "segment_description": "Recently joined and has uncertain long-term engagement.",
        "monthly_listening_hours": 3.0,
        "preferred_access_model": "Streaming",
        "churn_risk_level": "High",
    },
    {
        "segment_id": 6,
        "segment_name": "Genre Loyalist",
        "segment_description": "Strongly prefers one genre and similar recommendations.",
        "monthly_listening_hours": 13.0,
        "preferred_access_model": "Hybrid",
        "churn_risk_level": "Medium",
    },
    {
        "segment_id": 7,
        "segment_name": "Weekend Listener",
        "segment_description": "Concentrates most listening activity on weekends.",
        "monthly_listening_hours": 9.0,
        "preferred_access_model": "Streaming",
        "churn_risk_level": "Medium",
    },
]

PLATFORM_MODELS = [
    {
        "model_id": 1,
        "model_name": "Streaming Basic",
        "access_type": "Streaming",
        "monthly_price": 11.99,
        "monthly_hour_limit": 15,
        "monthly_credit_allowance": 0,
        "ownership_included": False,
    },
    {
        "model_id": 2,
        "model_name": "Ownership Credit",
        "access_type": "Ownership",
        "monthly_price": 14.95,
        "monthly_hour_limit": None,
        "monthly_credit_allowance": 1,
        "ownership_included": True,
    },
    {
        "model_id": 3,
        "model_name": "Hybrid Plus",
        "access_type": "Hybrid",
        "monthly_price": 19.99,
        "monthly_hour_limit": 20,
        "monthly_credit_allowance": 1,
        "ownership_included": True,
    },
]


def random_date(start: date, end: date) -> date:
    """Return a random date between start and end."""
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def generate_listener_segments() -> pd.DataFrame:
    return pd.DataFrame(SEGMENTS)


def generate_platform_models() -> pd.DataFrame:
    return pd.DataFrame(PLATFORM_MODELS)


def generate_narrators() -> pd.DataFrame:
    rows = []

    for narrator_id in range(1, NUM_NARRATORS + 1):
        experience_years = random.randint(1, 30)

        if experience_years >= 20:
            performance_tier = "Elite"
            average_rating = round(np.random.normal(4.6, 0.18), 2)
        elif experience_years >= 8:
            performance_tier = "Premium"
            average_rating = round(np.random.normal(4.3, 0.22), 2)
        else:
            performance_tier = "Standard"
            average_rating = round(np.random.normal(4.0, 0.28), 2)

        average_rating = min(max(average_rating, 2.5), 5.0)

        rows.append(
            {
                "narrator_id": narrator_id,
                "narrator_name": fake.name(),
                "gender": random.choice(["Female", "Male", "Non-binary"]),
                "experience_years": experience_years,
                "performance_tier": performance_tier,
                "average_rating": average_rating,
            }
        )

    return pd.DataFrame(rows)


def generate_books(narrators: pd.DataFrame) -> pd.DataFrame:
    rows = []
    narrator_ids = narrators["narrator_id"].tolist()
    narrator_rating_map = narrators.set_index("narrator_id")["average_rating"].to_dict()

    for book_id in range(1, NUM_BOOKS + 1):
        narrator_id = random.choice(narrator_ids)
        genre = random.choice(GENRES)
        duration_minutes = int(np.clip(np.random.normal(600, 240), 120, 1_800))

        narrator_effect = narrator_rating_map[narrator_id] - 4.0
        average_rating = round(
            np.clip(np.random.normal(4.0 + narrator_effect * 0.35, 0.35), 1, 5),
            2,
        )

        rows.append(
            {
                "book_id": book_id,
                "title": fake.catch_phrase(),
                "author_name": fake.name(),
                "narrator_id": narrator_id,
                "genre": genre,
                "duration_minutes": duration_minutes,
                "release_year": random.randint(2000, 2026),
                "language": random.choices(
                    ["English", "Spanish", "Hindi", "French"],
                    weights=[82, 7, 6, 5],
                    k=1,
                )[0],
                "average_rating": average_rating,
            }
        )

    return pd.DataFrame(rows)


def generate_users() -> pd.DataFrame:
    segment_weights = [24, 15, 14, 10, 12, 15, 10]
    rows = []

    for user_id in range(1, NUM_USERS + 1):
        segment = random.choices(SEGMENTS, weights=segment_weights, k=1)[0]
        signup_date = random_date(date(2023, 1, 1), date(2026, 6, 30))

        is_active_probability = {
            "Trial": 0.60,
            "Casual": 0.80,
            "Power": 0.95,
            "Collector": 0.93,
            "Rereader": 0.94,
            "Genre Loyalist": 0.88,
            "Weekend Listener": 0.82,
        }[segment["segment_name"]]

        rows.append(
            {
                "user_id": user_id,
                "signup_date": signup_date,
                "country": random.choices(
                    COUNTRIES,
                    weights=[55, 10, 12, 18, 5],
                    k=1,
                )[0],
                "age_group": random.choices(
                    AGE_GROUPS,
                    weights=[20, 35, 24, 14, 7],
                    k=1,
                )[0],
                "device_type": random.choices(
                    DEVICES,
                    weights=[55, 12, 8, 10, 15],
                    k=1,
                )[0],
                "preferred_genre": random.choice(GENRES),
                "segment_id": segment["segment_id"],
                "is_active": random.random() < is_active_probability,
            }
        )

    return pd.DataFrame(rows)


def choose_model_for_segment(segment_name: str) -> int:
    mapping = {
        "Casual": [1, 1, 1, 3],
        "Power": [1, 3, 3, 3],
        "Collector": [2, 2, 2, 3],
        "Rereader": [2, 2, 3],
        "Trial": [1, 1, 1, 3],
        "Genre Loyalist": [1, 3, 3],
        "Weekend Listener": [1, 1, 3],
    }
    return random.choice(mapping[segment_name])


def generate_subscriptions(
    users: pd.DataFrame,
    listener_segments: pd.DataFrame,
    platform_models: pd.DataFrame,
) -> pd.DataFrame:
    segment_name_map = listener_segments.set_index("segment_id")[
        "segment_name"
    ].to_dict()
    model_map = platform_models.set_index("model_id").to_dict("index")

    rows = []

    for subscription_id, user in enumerate(users.itertuples(), start=1):
        segment_name = segment_name_map[user.segment_id]
        model_id = choose_model_for_segment(segment_name)
        model = model_map[model_id]

        if user.is_active:
            status = random.choices(
                ["Active", "Paused", "Trial"],
                weights=[87, 6, 7],
                k=1,
            )[0]
        else:
            status = "Cancelled"

        start_date = max(
            user.signup_date,
            random_date(user.signup_date, date(2026, 6, 30)),
        )

        cancellation_date = None
        if status == "Cancelled":
            cancellation_date = random_date(start_date, date(2026, 6, 30))

        if model["access_type"] in {"Ownership", "Hybrid"}:
            unused_credits = random.choices(
                [0, 1, 2, 3],
                weights=[48, 30, 15, 7],
                k=1,
            )[0]

            if segment_name == "Collector":
                unused_credits = random.choices(
                    [0, 1, 2],
                    weights=[70, 25, 5],
                    k=1,
                )[0]
        else:
            unused_credits = 0

        rows.append(
            {
                "subscription_id": subscription_id,
                "user_id": user.user_id,
                "model_id": model_id,
                "plan_name": model["model_name"],
                "monthly_price": model["monthly_price"],
                "subscription_status": status,
                "start_date": start_date,
                "cancellation_date": cancellation_date,
                "unused_credits": unused_credits,
            }
        )

    return pd.DataFrame(rows)


def choose_book_for_user(
    user: pd.Series,
    books: pd.DataFrame,
    segment_name: str,
) -> pd.Series:
    if segment_name == "Genre Loyalist" or random.random() < 0.55:
        matching_books = books[books["genre"] == user["preferred_genre"]]
        if not matching_books.empty:
            return matching_books.sample(1, random_state=random.randint(1, 1_000_000)).iloc[0]

    return books.sample(1, random_state=random.randint(1, 1_000_000)).iloc[0]


def generate_listening_sessions(
    users: pd.DataFrame,
    books: pd.DataFrame,
    listener_segments: pd.DataFrame,
) -> pd.DataFrame:
    user_map = users.set_index("user_id")
    segment_name_map = listener_segments.set_index("segment_id")[
        "segment_name"
    ].to_dict()

    segment_weights = {
        "Casual": 0.70,
        "Power": 2.20,
        "Collector": 1.10,
        "Rereader": 1.35,
        "Trial": 0.45,
        "Genre Loyalist": 1.20,
        "Weekend Listener": 0.90,
    }

    weighted_user_ids = []
    weighted_values = []

    for user in users.itertuples():
        segment_name = segment_name_map[user.segment_id]
        weighted_user_ids.append(user.user_id)
        weighted_values.append(segment_weights[segment_name])

    rows = []

    for session_id in range(1, NUM_LISTENING_SESSIONS + 1):
        user_id = random.choices(
            weighted_user_ids,
            weights=weighted_values,
            k=1,
        )[0]

        user = user_map.loc[user_id]
        segment_name = segment_name_map[user["segment_id"]]
        book = choose_book_for_user(user, books, segment_name)

        if segment_name == "Weekend Listener":
            session_date = random_date(date(2025, 7, 1), date(2026, 6, 30))
            while session_date.weekday() < 5:
                session_date = random_date(date(2025, 7, 1), date(2026, 6, 30))
        else:
            session_date = random_date(date(2025, 7, 1), date(2026, 6, 30))

        minutes_mean = {
            "Casual": 35,
            "Power": 95,
            "Collector": 65,
            "Rereader": 75,
            "Trial": 25,
            "Genre Loyalist": 70,
            "Weekend Listener": 85,
        }[segment_name]

        minutes_listened = int(
            np.clip(np.random.normal(minutes_mean, 25), 5, 240)
        )

        duration = book["duration_minutes"]
        completion_base = (minutes_listened / duration) * 100

        if duration > 900:
            completion_base *= 0.82

        if segment_name in {"Power", "Rereader"}:
            completion_base *= 1.25
        elif segment_name == "Trial":
            completion_base *= 0.70

        completion_percentage = round(
            float(np.clip(completion_base + np.random.normal(20, 15), 1, 100)),
            2,
        )

        rows.append(
            {
                "session_id": session_id,
                "user_id": user_id,
                "book_id": int(book["book_id"]),
                "session_date": session_date,
                "minutes_listened": minutes_listened,
                "chapter_number": random.randint(1, 40),
                "completion_percentage": completion_percentage,
                "device_type": user["device_type"],
                "session_day_type": (
                    "Weekend" if session_date.weekday() >= 5 else "Weekday"
                ),
            }
        )

    return pd.DataFrame(rows)


def generate_book_ownership(
    users: pd.DataFrame,
    books: pd.DataFrame,
    subscriptions: pd.DataFrame,
    listener_segments: pd.DataFrame,
) -> pd.DataFrame:
    segment_name_map = listener_segments.set_index("segment_id")[
        "segment_name"
    ].to_dict()

    eligible = subscriptions[
        subscriptions["model_id"].isin([2, 3])
    ].merge(
        users[["user_id", "segment_id"]],
        on="user_id",
        how="left",
    )

    rows = []
    ownership_id = 1

    for record in eligible.itertuples():
        segment_name = segment_name_map[record.segment_id]

        number_owned = {
            "Collector": random.randint(3, 10),
            "Rereader": random.randint(2, 8),
            "Power": random.randint(1, 5),
        }.get(segment_name, random.randint(0, 3))

        sampled_books = books.sample(
            n=min(number_owned, len(books)),
            random_state=random.randint(1, 1_000_000),
        )

        for book in sampled_books.itertuples():
            method = random.choices(
                ["Credit", "Direct Purchase", "Gift", "Promotion"],
                weights=[60, 22, 8, 10],
                k=1,
            )[0]

            rows.append(
                {
                    "ownership_id": ownership_id,
                    "user_id": record.user_id,
                    "book_id": book.book_id,
                    "acquisition_date": random_date(
                        record.start_date,
                        date(2026, 6, 30),
                    ),
                    "acquisition_method": method,
                    "credits_used": 1 if method == "Credit" else 0,
                    "purchase_price": (
                        round(random.uniform(7.99, 29.99), 2)
                        if method == "Direct Purchase"
                        else 0.0
                    ),
                    "times_replayed": (
                        random.randint(1, 6)
                        if segment_name == "Rereader"
                        else random.randint(0, 2)
                    ),
                }
            )
            ownership_id += 1

    return pd.DataFrame(rows)


def generate_ratings(
    listening_sessions: pd.DataFrame,
    books: pd.DataFrame,
) -> pd.DataFrame:
    completed_sessions = listening_sessions[
        listening_sessions["completion_percentage"] >= 35
    ]

    source = completed_sessions.sample(
        n=min(NUM_RATINGS, len(completed_sessions)),
        random_state=SEED,
    )

    book_rating_map = books.set_index("book_id")["average_rating"].to_dict()
    rows = []

    for rating_id, session in enumerate(source.itertuples(), start=1):
        expected_rating = book_rating_map[session.book_id]
        rating_score = int(
            np.clip(round(np.random.normal(expected_rating, 0.8)), 1, 5)
        )

        if rating_score >= 4:
            sentiment = "Positive"
        elif rating_score == 3:
            sentiment = "Neutral"
        else:
            sentiment = "Negative"

        rows.append(
            {
                "rating_id": rating_id,
                "user_id": session.user_id,
                "book_id": session.book_id,
                "rating_score": rating_score,
                "review_sentiment": sentiment,
                "rating_date": session.session_date,
            }
        )

    return pd.DataFrame(rows)


def generate_recommendations(
    users: pd.DataFrame,
    books: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    for recommendation_id in range(1, NUM_RECOMMENDATIONS + 1):
        user = users.sample(
            1,
            random_state=random.randint(1, 1_000_000),
        ).iloc[0]

        source = random.choices(
            ["Personalized", "Homepage", "Genre", "Trending"],
            weights=[40, 25, 22, 13],
            k=1,
        )[0]

        if source in {"Personalized", "Genre"}:
            matching = books[books["genre"] == user["preferred_genre"]]
            book = (
                matching.sample(
                    1,
                    random_state=random.randint(1, 1_000_000),
                ).iloc[0]
                if not matching.empty
                else books.sample(1).iloc[0]
            )
        else:
            book = books.sample(
                1,
                random_state=random.randint(1, 1_000_000),
            ).iloc[0]

        click_probability = {
            "Personalized": 0.58,
            "Genre": 0.48,
            "Homepage": 0.32,
            "Trending": 0.27,
        }[source]

        clicked = random.random() < click_probability
        started = clicked and random.random() < 0.68
        completed = started and random.random() < 0.42

        rows.append(
            {
                "recommendation_id": recommendation_id,
                "user_id": int(user["user_id"]),
                "book_id": int(book["book_id"]),
                "recommendation_source": source,
                "recommendation_date": random_date(
                    date(2025, 7, 1),
                    date(2026, 6, 30),
                ),
                "clicked": clicked,
                "started_listening": started,
                "completed": completed,
            }
        )

    return pd.DataFrame(rows)


def validate_dataset(datasets: dict[str, pd.DataFrame]) -> None:
    expected_counts = {
        "users": NUM_USERS,
        "books": NUM_BOOKS,
        "narrators": NUM_NARRATORS,
        "listening_sessions": NUM_LISTENING_SESSIONS,
        "ratings": NUM_RATINGS,
        "recommendations": NUM_RECOMMENDATIONS,
        "listener_segments": len(SEGMENTS),
        "platform_models": len(PLATFORM_MODELS),
    }

    for name, expected_count in expected_counts.items():
        actual_count = len(datasets[name])
        if actual_count != expected_count:
            raise ValueError(
                f"{name}: expected {expected_count} rows, found {actual_count}"
            )

    if datasets["users"]["user_id"].duplicated().any():
        raise ValueError("Duplicate user IDs found.")

    if datasets["books"]["book_id"].duplicated().any():
        raise ValueError("Duplicate book IDs found.")

    valid_user_ids = set(datasets["users"]["user_id"])
    valid_book_ids = set(datasets["books"]["book_id"])

    if not set(datasets["listening_sessions"]["user_id"]).issubset(valid_user_ids):
        raise ValueError("Listening sessions contain invalid user IDs.")

    if not set(datasets["listening_sessions"]["book_id"]).issubset(valid_book_ids):
        raise ValueError("Listening sessions contain invalid book IDs.")


def save_datasets(datasets: dict[str, pd.DataFrame]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for name, dataframe in datasets.items():
        output_path = OUTPUT_DIR / f"{name}.csv"
        dataframe.to_csv(output_path, index=False)
        print(f"Saved {name:<20} {len(dataframe):>6} rows -> {output_path}")


def main() -> None:
    listener_segments = generate_listener_segments()
    platform_models = generate_platform_models()
    narrators = generate_narrators()
    books = generate_books(narrators)
    users = generate_users()

    subscriptions = generate_subscriptions(
        users,
        listener_segments,
        platform_models,
    )

    listening_sessions = generate_listening_sessions(
        users,
        books,
        listener_segments,
    )

    book_ownership = generate_book_ownership(
        users,
        books,
        subscriptions,
        listener_segments,
    )

    ratings = generate_ratings(
        listening_sessions,
        books,
    )

    recommendations = generate_recommendations(
        users,
        books,
    )

    datasets = {
        "listener_segments": listener_segments,
        "platform_models": platform_models,
        "narrators": narrators,
        "books": books,
        "users": users,
        "subscriptions": subscriptions,
        "book_ownership": book_ownership,
        "listening_sessions": listening_sessions,
        "ratings": ratings,
        "recommendations": recommendations,
    }

    validate_dataset(datasets)
    save_datasets(datasets)

    print("\nSynthetic dataset generation completed successfully.")


if __name__ == "__main__":
    main()