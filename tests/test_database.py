import pytest
from db.database import Database, Post


@pytest.fixture
def db():
    d = Database(":memory:")
    d.init_db()
    d.seed_agents([{
        "id": "anxiety",
        "emotion_kr": "불안",
        "persona_prompt": "test persona",
        "aesthetic_prompt": "test aesthetic",
        "post_frequency": 2.0,
    }])
    return d


def test_init_creates_tables(db):
    tables = db.conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    names = {r[0] for r in tables}
    assert {"agents", "posts", "interactions", "follows"} <= names


def test_save_post_returns_id(db):
    post_id = db.save_post("anxiety", "test caption", None, tick=0)
    assert isinstance(post_id, int)
    assert post_id > 0


def test_get_recent_posts_empty(db):
    assert db.get_recent_posts() == []


def test_get_recent_posts_returns_post(db):
    db.save_post("anxiety", "hello", None, tick=1)
    posts = db.get_recent_posts()
    assert len(posts) == 1
    assert posts[0].agent_id == "anxiety"
    assert posts[0].caption == "hello"
    assert isinstance(posts[0], Post)


def test_get_recent_posts_excludes_self(db):
    db.save_post("anxiety", "hello", None, tick=1)
    posts = db.get_recent_posts(exclude_agent_id="anxiety")
    assert posts == []


def test_get_recent_stimuli_zero_when_none(db):
    count = db.get_recent_stimuli("anxiety", since_tick=0)
    assert count == 0


def test_get_recent_stimuli_counts_interactions(db):
    db.seed_agents([{
        "id": "excitement",
        "emotion_kr": "설렘",
        "persona_prompt": "p",
        "aesthetic_prompt": "a",
        "post_frequency": 3.0,
    }])
    post_id = db.save_post("anxiety", "caption", None, tick=2)
    db.save_interaction("excitement", post_id, "like", None, tick=3)
    db.save_interaction("excitement", post_id, "comment", "wow", tick=3)
    assert db.get_recent_stimuli("anxiety", since_tick=2) == 2


def test_get_recent_stimuli_ignores_old(db):
    db.seed_agents([{
        "id": "excitement",
        "emotion_kr": "설렘",
        "persona_prompt": "p",
        "aesthetic_prompt": "a",
        "post_frequency": 3.0,
    }])
    post_id = db.save_post("anxiety", "caption", None, tick=0)
    db.save_interaction("excitement", post_id, "like", None, tick=1)
    assert db.get_recent_stimuli("anxiety", since_tick=5) == 0


def test_get_all_posts_filter_agent(db):
    db.save_post("anxiety", "a1", None, tick=0)
    db.save_post("anxiety", "a2", None, tick=1)
    posts = db.get_all_posts(agent_id="anxiety")
    assert len(posts) == 2
    posts_other = db.get_all_posts(agent_id="excitement")
    assert posts_other == []


def test_get_all_posts_filter_since_tick(db):
    db.save_post("anxiety", "old", None, tick=0)
    db.save_post("anxiety", "new", None, tick=5)
    posts = db.get_all_posts(since_tick=3)
    assert len(posts) == 1
    assert posts[0].caption == "new"


def test_get_interactions_for_post(db):
    db.seed_agents([{
        "id": "excitement",
        "emotion_kr": "설렘",
        "persona_prompt": "p",
        "aesthetic_prompt": "a",
        "post_frequency": 3.0,
    }])
    post_id = db.save_post("anxiety", "cap", None, tick=0)
    db.save_interaction("excitement", post_id, "like", None, tick=1)
    db.save_interaction("excitement", post_id, "comment", "nice", tick=1)
    interactions = db.get_interactions_for_post(post_id)
    assert len(interactions) == 2
    types = {i["type"] for i in interactions}
    assert types == {"like", "comment"}


def test_get_max_tick_none_when_empty(db):
    assert db.get_max_tick() is None


def test_get_max_tick_returns_max(db):
    db.save_post("anxiety", "a", None, tick=3)
    db.save_post("anxiety", "b", None, tick=7)
    assert db.get_max_tick() == 7


def test_update_quality_score(db):
    post_id = db.save_post("anxiety", "cap", None, tick=0)
    db.update_quality_score(post_id, 0.85)
    posts = db.get_all_posts(agent_id="anxiety")
    assert posts[0].quality_score == pytest.approx(0.85)


def test_get_agent_stats_empty(db):
    stats = db.get_agent_stats()
    assert "anxiety" in stats
    assert stats["anxiety"]["post_count"] == 0
    assert stats["anxiety"]["received_likes"] == 0


def test_get_agent_stats_counts(db):
    post_id = db.save_post("anxiety", "cap", None, tick=0)
    db.save_interaction("excitement", post_id, "like", None, tick=1)
    db.save_interaction("excitement", post_id, "comment", "reply", tick=1)
    stats = db.get_agent_stats()
    assert stats["anxiety"]["post_count"] == 1
    assert stats["anxiety"]["received_likes"] == 1
    assert stats["anxiety"]["received_comments"] == 1
