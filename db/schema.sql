CREATE TABLE IF NOT EXISTS agents (
    id               TEXT    PRIMARY KEY,
    emotion_kr       TEXT    NOT NULL,
    persona_prompt   TEXT    NOT NULL,
    aesthetic_prompt TEXT    NOT NULL,
    post_frequency   REAL    NOT NULL
);

CREATE TABLE IF NOT EXISTS posts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id      TEXT    NOT NULL REFERENCES agents(id),
    image_path    TEXT,
    caption       TEXT    NOT NULL,
    tick          INTEGER NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ig_posted     BOOLEAN DEFAULT FALSE,
    quality_score REAL
);

CREATE TABLE IF NOT EXISTS interactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent  TEXT    NOT NULL REFERENCES agents(id),
    to_post     INTEGER NOT NULL REFERENCES posts(id),
    type        TEXT    NOT NULL CHECK(type IN ('like', 'comment')),
    content     TEXT,
    tick        INTEGER NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS follows (
    follower_agent  TEXT NOT NULL REFERENCES agents(id),
    following_agent TEXT NOT NULL REFERENCES agents(id),
    PRIMARY KEY (follower_agent, following_agent)
);
