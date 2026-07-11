-- ListenLens Database Schema
-- Audiobook Strategy Intelligence Platform

CREATE TABLE IF NOT EXISTS narrators (
    narrator_id INTEGER PRIMARY KEY,
    narrator_name VARCHAR NOT NULL,
    gender VARCHAR,
    experience_years INTEGER,
    performance_tier VARCHAR,
    average_rating DECIMAL(3, 2)
);

CREATE TABLE IF NOT EXISTS books (
    book_id INTEGER PRIMARY KEY,
    title VARCHAR NOT NULL,
    author_name VARCHAR NOT NULL,
    narrator_id INTEGER,
    genre VARCHAR NOT NULL,
    duration_minutes INTEGER NOT NULL,
    release_year INTEGER,
    language VARCHAR DEFAULT 'English',
    average_rating DECIMAL(3, 2),
    FOREIGN KEY (narrator_id) REFERENCES narrators(narrator_id)
);

CREATE TABLE IF NOT EXISTS listener_segments (
    segment_id INTEGER PRIMARY KEY,
    segment_name VARCHAR UNIQUE NOT NULL,
    segment_description VARCHAR,
    monthly_listening_hours DECIMAL(6, 2),
    preferred_access_model VARCHAR,
    churn_risk_level VARCHAR
);

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    signup_date DATE NOT NULL,
    country VARCHAR,
    age_group VARCHAR,
    device_type VARCHAR,
    preferred_genre VARCHAR,
    segment_id INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (segment_id) REFERENCES listener_segments(segment_id)
);

CREATE TABLE IF NOT EXISTS platform_models (
    model_id INTEGER PRIMARY KEY,
    model_name VARCHAR UNIQUE NOT NULL,
    access_type VARCHAR NOT NULL,
    monthly_price DECIMAL(8, 2),
    monthly_hour_limit INTEGER,
    monthly_credit_allowance INTEGER,
    ownership_included BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS subscriptions (
    subscription_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    model_id INTEGER NOT NULL,
    plan_name VARCHAR NOT NULL,
    monthly_price DECIMAL(8, 2),
    subscription_status VARCHAR NOT NULL,
    start_date DATE NOT NULL,
    cancellation_date DATE,
    unused_credits INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (model_id) REFERENCES platform_models(model_id)
);

CREATE TABLE IF NOT EXISTS book_ownership (
    ownership_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    acquisition_date DATE NOT NULL,
    acquisition_method VARCHAR NOT NULL,
    credits_used INTEGER DEFAULT 0,
    purchase_price DECIMAL(8, 2),
    times_replayed INTEGER DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);

CREATE TABLE IF NOT EXISTS listening_sessions (
    session_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    session_date DATE NOT NULL,
    minutes_listened INTEGER NOT NULL,
    chapter_number INTEGER,
    completion_percentage DECIMAL(5, 2),
    device_type VARCHAR,
    session_day_type VARCHAR,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);

CREATE TABLE IF NOT EXISTS ratings (
    rating_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    rating_score INTEGER NOT NULL CHECK (rating_score BETWEEN 1 AND 5),
    review_sentiment VARCHAR,
    rating_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);

CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    book_id INTEGER NOT NULL,
    recommendation_source VARCHAR NOT NULL,
    recommendation_date DATE NOT NULL,
    clicked BOOLEAN DEFAULT FALSE,
    started_listening BOOLEAN DEFAULT FALSE,
    completed BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (book_id) REFERENCES books(book_id)
);