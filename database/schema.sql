CREATE DATABASE IF NOT EXISTS recommendation_system;
USE recommendation_system;

-- =========================
-- USERS
-- =========================
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(32) NOT NULL UNIQUE,
    gender VARCHAR(16),
    age INT,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- MOVIES
-- =========================
CREATE TABLE IF NOT EXISTS movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tmdb_id INT UNIQUE,
    title VARCHAR(128) NOT NULL,
    genres JSON,
    overview TEXT,
    release_date DATE,
    vote_average DECIMAL(4,2),
    vote_count INT,
    runtime INT,
    tagline VARCHAR(256),
    director VARCHAR(64),
    poster_path VARCHAR(64),
    backdrop_path VARCHAR(64),
    score FLOAT
);

-- =========================
-- ACTORS
-- =========================
CREATE TABLE IF NOT EXISTS actors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tmdb_id INT UNIQUE,
    name VARCHAR(64) NOT NULL,
    profile_path VARCHAR(64)
);

-- =========================
-- MOVIE_ACTORS
-- =========================
CREATE TABLE IF NOT EXISTS movie_actors (
    movie_id INT,
    actor_id INT,
    PRIMARY KEY (movie_id, actor_id),
    FOREIGN KEY (movie_id) REFERENCES movies(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (actor_id) REFERENCES actors(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =========================
-- RATINGS
-- =========================
CREATE TABLE IF NOT EXISTS ratings (
    user_id INT,
    movie_id INT,
    rating DECIMAL(2,1) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =========================
-- PERSONALITIES
-- =========================
CREATE TABLE IF NOT EXISTS personalities (
    user_id INT PRIMARY KEY,
    openness DECIMAL(3,2) NOT NULL,
    conscientiousness DECIMAL(3,2) NOT NULL,
    extraversion DECIMAL(3,2) NOT NULL,
    agreeableness DECIMAL(3,2) NOT NULL,
    neuroticism DECIMAL(3,2) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =========================
-- WATCHLIST
-- =========================
CREATE TABLE IF NOT EXISTS watchlist (
    user_id INT,
    movie_id INT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, movie_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (movie_id) REFERENCES movies(id)
        ON DELETE CASCADE ON UPDATE CASCADE
);

-- =========================
-- SURVEY
-- =========================
CREATE TABLE IF NOT EXISTS survey_responses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    question_id VARCHAR(10) NOT NULL,
    answer TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE KEY unique_response (user_id, question_id)
);