import pytest
from fastapi.testclient import TestClient
from db.database import Database
from api.main import app
from api.deps import get_db


@pytest.fixture
def client(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    db.init_db()
    db.seed_agents([
        {"id": "anxiety", "emotion_kr": "불안", "persona_prompt": "p",
         "aesthetic_prompt": "a", "post_frequency": 2.0},
        {"id": "excitement", "emotion_kr": "설렘", "persona_prompt": "p",
         "aesthetic_prompt": "a", "post_frequency": 3.0},
    ])
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_get_agents(client):
    r = client.get("/api/agents")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert data[0]["id"] == "anxiety"
    assert "emotion_kr" in data[0]
    assert "post_frequency" in data[0]


def test_get_posts_empty(client):
    r = client.get("/api/posts")
    assert r.status_code == 200
    assert r.json() == []


def test_get_posts_returns_data(client, tmp_path):
    db = client.app.dependency_overrides[get_db]()
    db.save_post("anxiety", "두렵다.", None, tick=1)
    r = client.get("/api/posts")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["caption"] == "두렵다."
    assert data[0]["agent_id"] == "anxiety"
    assert data[0]["tick"] == 1
    assert data[0]["quality_score"] is None


def test_get_posts_filter_by_agent(client):
    db = client.app.dependency_overrides[get_db]()
    db.save_post("anxiety", "cap1", None, tick=0)
    db.save_post("excitement", "cap2", None, tick=1)
    r = client.get("/api/posts?agent_id=anxiety")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["agent_id"] == "anxiety"


def test_patch_score(client):
    db = client.app.dependency_overrides[get_db]()
    post_id = db.save_post("anxiety", "cap", None, tick=0)
    r = client.patch(f"/api/posts/{post_id}/score", json={"score": 0.85})
    assert r.status_code == 200
    assert r.json()["score"] == pytest.approx(0.85)
    posts = db.get_all_posts(agent_id="anxiety")
    assert posts[0].quality_score == pytest.approx(0.85)


def test_get_post_by_id(client):
    db = client.app.dependency_overrides[get_db]()
    post_id = db.save_post("anxiety", "cap", None, tick=2)
    r = client.get(f"/api/posts/{post_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == post_id
    assert data["tick"] == 2


def test_get_post_not_found(client):
    r = client.get("/api/posts/999")
    assert r.status_code == 404


def test_get_graph(client):
    r = client.get("/api/graph")
    assert r.status_code == 200
    data = r.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) == 2
    node_ids = [n["id"] for n in data["nodes"]]
    assert "anxiety" in node_ids


def test_get_stats(client):
    db = client.app.dependency_overrides[get_db]()
    post_id = db.save_post("anxiety", "cap", None, tick=0)
    db.save_interaction("excitement", post_id, "like", None, tick=1)
    r = client.get("/api/stats")
    assert r.status_code == 200
    data = r.json()
    assert data["anxiety"]["post_count"] == 1
    assert data["anxiety"]["received_likes"] == 1
