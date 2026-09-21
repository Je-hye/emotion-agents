import pytest
from unittest.mock import MagicMock

from db.database import Database, Post
from simulation.feed import format_post, print_feed


@pytest.fixture
def db():
    d = Database(":memory:")
    d.init_db()
    d.seed_agents([
        {"id": "anxiety", "emotion_kr": "불안", "persona_prompt": "p",
         "aesthetic_prompt": "a", "post_frequency": 2.0},
        {"id": "excitement", "emotion_kr": "설렘", "persona_prompt": "p",
         "aesthetic_prompt": "a", "post_frequency": 3.0},
    ])
    return d


def test_format_post_basic():
    post = Post(id=1, agent_id="anxiety", caption="두렵다.", image_path=None, tick=3)
    output = format_post(post, interactions=[])
    assert "[tick 3] @anxiety" in output
    assert "두렵다." in output


def test_format_post_with_image():
    post = Post(id=1, agent_id="anxiety", caption="caption", image_path="data/images/anxiety_3.png", tick=3)
    output = format_post(post, interactions=[])
    assert "data/images/anxiety_3.png" in output


def test_format_post_with_like():
    post = Post(id=1, agent_id="anxiety", caption="caption", image_path=None, tick=3)
    interactions = [{"from_agent": "excitement", "type": "like", "content": None}]
    output = format_post(post, interactions)
    assert "@excitement" in output
    assert "❤" in output


def test_format_post_with_comment():
    post = Post(id=1, agent_id="anxiety", caption="caption", image_path=None, tick=3)
    interactions = [{"from_agent": "excitement", "type": "comment", "content": "나도."}]
    output = format_post(post, interactions)
    assert "💬" in output
    assert "나도." in output


def test_print_feed_filters_by_agent(db, capsys):
    db.save_post("anxiety", "anxiety post", None, tick=0)
    db.save_post("excitement", "excitement post", None, tick=1)
    print_feed(db, agent_id="anxiety")
    captured = capsys.readouterr()
    assert "anxiety post" in captured.out
    assert "excitement post" not in captured.out


def test_print_feed_filters_by_since_tick(db, capsys):
    db.save_post("anxiety", "old post", None, tick=0)
    db.save_post("anxiety", "new post", None, tick=5)
    print_feed(db, since_tick=3)
    captured = capsys.readouterr()
    assert "new post" in captured.out
    assert "old post" not in captured.out
