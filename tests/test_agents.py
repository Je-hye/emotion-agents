import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from db.database import Database, Post
from agents.base import AgentBase


@pytest.fixture
def db():
    d = Database(":memory:")
    d.init_db()
    d.seed_agents([
        {"id": "anxiety", "emotion_kr": "불안", "persona_prompt": "p1",
         "aesthetic_prompt": "a1", "post_frequency": 2.0},
        {"id": "excitement", "emotion_kr": "설렘", "persona_prompt": "p2",
         "aesthetic_prompt": "a2", "post_frequency": 3.0},
    ])
    return d


@pytest.fixture
def anxiety_agent(db):
    return AgentBase(
        agent_id="anxiety",
        emotion_kr="불안",
        persona_prompt="persona",
        aesthetic_prompt="aesthetic",
        post_frequency=2.0,
        db=db,
    )


def test_should_post_returns_true_when_below_prob(anxiety_agent):
    with patch("agents.base.random.random", return_value=0.01):
        assert anxiety_agent.should_post(tick=0) is True


def test_should_post_returns_false_when_above_prob(anxiety_agent):
    with patch("agents.base.random.random", return_value=0.99):
        assert anxiety_agent.should_post(tick=0) is False


def test_should_post_stimulus_increases_probability(anxiety_agent, db):
    post_id = db.save_post("anxiety", "cap", None, tick=0)
    for _ in range(5):
        db.save_interaction("excitement", post_id, "like", None, tick=1)
    # base_prob = 0.5, multiplier = 1.5, prob = 0.75
    with patch("agents.base.random.random", return_value=0.7):
        assert anxiety_agent.should_post(tick=2) is True


@pytest.mark.asyncio
async def test_maybe_post_saves_to_db(anxiety_agent, db):
    with patch("agents.base.random.random", return_value=0.01), \
         patch("agents.base.generate_caption", AsyncMock(return_value="test caption")), \
         patch("agents.base.generate_image", AsyncMock(return_value="data/images/anxiety_1.png")):
        post_id = await anxiety_agent.maybe_post(tick=1)

    assert post_id is not None
    posts = db.get_all_posts(agent_id="anxiety")
    assert len(posts) == 1
    assert posts[0].caption == "test caption"
    assert posts[0].image_path == "data/images/anxiety_1.png"


@pytest.mark.asyncio
async def test_maybe_post_returns_none_when_skipping(anxiety_agent):
    with patch("agents.base.random.random", return_value=0.99):
        result = await anxiety_agent.maybe_post(tick=0)
    assert result is None


@pytest.mark.asyncio
async def test_interact_likes_other_agent_post(anxiety_agent, db):
    db.save_post("excitement", "exciting post", None, tick=0)

    with patch("agents.base.random.random", side_effect=[0.1, 0.9]):
        await anxiety_agent.interact(tick=1)

    interactions = db.conn.execute(
        "SELECT type FROM interactions WHERE from_agent='anxiety'"
    ).fetchall()
    assert len(interactions) == 1
    assert interactions[0][0] == "like"


@pytest.mark.asyncio
async def test_interact_comments_on_other_agent_post(anxiety_agent, db):
    db.save_post("excitement", "exciting post", None, tick=0)

    with patch("agents.base.random.random", side_effect=[0.1, 0.1]), \
         patch("agents.base.generate_comment", AsyncMock(return_value="나도 그래.")):
        await anxiety_agent.interact(tick=1)

    interactions = db.conn.execute(
        "SELECT type, content FROM interactions WHERE from_agent='anxiety'"
    ).fetchall()
    assert len(interactions) == 1
    assert interactions[0][0] == "comment"
    assert interactions[0][1] == "나도 그래."


@pytest.mark.asyncio
async def test_interact_ignores_own_posts(anxiety_agent, db):
    db.save_post("anxiety", "own post", None, tick=0)
    with patch("agents.base.random.random", return_value=0.01):
        await anxiety_agent.interact(tick=1)
    interactions = db.conn.execute("SELECT * FROM interactions").fetchall()
    assert len(interactions) == 0
