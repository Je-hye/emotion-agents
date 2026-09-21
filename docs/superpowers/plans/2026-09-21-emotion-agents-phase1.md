# emotion-agents Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 두 감정 에이전트(anxiety, excitement)가 SQLite DB에 캡션+이미지를 포스팅하고 서로 인터랙션하는 tick 기반 로컬 시뮬레이션을 구축한다.

**Architecture:** asyncio 기반 tick 루프에서 모든 에이전트가 병렬로 포스팅·인터랙션을 수행한다. 캡션은 Claude API(claude-haiku-4-5-20251001), 이미지는 DALL-E 3으로 생성하고 로컬에 저장한다. DB는 SQLite이며 표준 라이브러리만 사용한다.

**Tech Stack:** Python 3.11+, anthropic SDK, openai SDK, httpx, python-dotenv, pytest, pytest-asyncio

**Spec:** docs/superpowers/specs/2026-09-21-emotion-agents-design.md

## Global Constraints

- Python 3.11+
- 모델: claude-haiku-4-5-20251001 (캡션/댓글), dall-e-3 / 1024x1024 (이미지)
- DB: SQLite (sqlite3 표준 라이브러리)
- 비동기: asyncio (aiosqlite 사용 안 함 — sqlite3 호출은 동기, 충분히 빠름)
- 테스트: pytest + pytest-asyncio, 외부 API는 unittest.mock.patch로 대체
- 이미지 저장: data/images/{agent_id}_{tick}.png
- .env 파일에서 ANTHROPIC_API_KEY, OPENAI_API_KEY 로드

---

## File Map

| 파일 | 역할 |
|------|------|
| `requirements.txt` | 의존성 |
| `.env.example` | 환경 변수 템플릿 |
| `.gitignore` | .env, data/images/, *.db 제외 |
| `pytest.ini` | asyncio_mode = auto |
| `db/schema.sql` | CREATE TABLE 4개 |
| `db/database.py` | Database 클래스 + Post dataclass |
| `config.py` | AFFINITIES, AGENTS 리스트, FOLLOWS, 상수 |
| `agents/anxiety.py` | anxiety 프롬프트 상수 |
| `agents/excitement.py` | excitement 프롬프트 상수 |
| `agents/base.py` | AgentBase: 포스팅·인터랙션 결정 |
| `services/caption.py` | Claude API 캡션·댓글 생성 |
| `services/image.py` | DALL-E 3 이미지 생성·저장 |
| `simulation/engine.py` | SimulationEngine: asyncio tick 루프 |
| `simulation/feed.py` | 피드 출력 포매터 |
| `cli.py` | CLI entrypoint (run / feed) |
| `tests/test_database.py` | DB 레이어 테스트 |
| `tests/test_agents.py` | AgentBase 테스트 |
| `tests/test_caption.py` | 캡션 서비스 테스트 |
| `tests/test_image.py` | 이미지 서비스 테스트 |
| `tests/test_engine.py` | 엔진 테스트 |
| `tests/test_feed.py` | 피드 포매터 테스트 |

---

### Task 1: Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `pytest.ini`
- Create: `db/__init__.py`, `agents/__init__.py`, `services/__init__.py`, `simulation/__init__.py`, `tests/__init__.py`

**Interfaces:**
- Produces: 설치 가능한 프로젝트 환경, `pytest` 실행 가능

- [ ] **Step 1: requirements.txt 작성**

```
anthropic>=0.40.0
openai>=1.50.0
httpx>=0.27.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
```

- [ ] **Step 2: .env.example 작성**

```
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

- [ ] **Step 3: .gitignore 작성**

```
.env
*.db
data/images/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 4: pytest.ini 작성**

```ini
[pytest]
asyncio_mode = auto
```

- [ ] **Step 5: 패키지 __init__.py 생성**

```bash
touch db/__init__.py agents/__init__.py services/__init__.py simulation/__init__.py tests/__init__.py
```

- [ ] **Step 6: 의존성 설치**

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

- [ ] **Step 7: pytest 실행 확인**

```bash
pytest --collect-only
```

Expected: "no tests ran" 또는 "0 items"

- [ ] **Step 8: 커밋**

```bash
git add requirements.txt .env.example .gitignore pytest.ini db/__init__.py agents/__init__.py services/__init__.py simulation/__init__.py tests/__init__.py
git commit -m "chore: project scaffolding"
```

---

### Task 2: DB Layer

**Files:**
- Create: `db/schema.sql`
- Create: `db/database.py`
- Create: `tests/test_database.py`

**Interfaces:**
- Produces:
  - `Post(id: int, agent_id: str, caption: str, image_path: Optional[str], tick: int)`
  - `Database(db_path: str = "emotion_agents.db")`
  - `Database.init_db() -> None`
  - `Database.seed_agents(agents_data: List[dict]) -> None`
  - `Database.seed_follows(follows: List[tuple]) -> None`
  - `Database.save_post(agent_id: str, caption: str, image_path: Optional[str], tick: int) -> int`
  - `Database.save_interaction(from_agent: str, to_post: int, type: str, content: Optional[str], tick: int) -> None`
  - `Database.get_recent_posts(exclude_agent_id: Optional[str] = None, limit: int = 10) -> List[Post]`
  - `Database.get_recent_stimuli(agent_id: str, since_tick: int) -> int`
  - `Database.get_all_posts(agent_id: Optional[str] = None, since_tick: Optional[int] = None) -> List[Post]`
  - `Database.get_interactions_for_post(post_id: int) -> List[dict]`
  - `Database.get_max_tick() -> Optional[int]`

- [ ] **Step 1: schema.sql 작성**

```sql
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
```

- [ ] **Step 2: 실패 테스트 작성 (tests/test_database.py)**

```python
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
```

- [ ] **Step 3: 테스트 실패 확인**

```bash
pytest tests/test_database.py -v
```

Expected: ImportError 또는 모든 테스트 FAIL

- [ ] **Step 4: database.py 구현**

```python
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Post:
    id: int
    agent_id: str
    caption: str
    image_path: Optional[str]
    tick: int


class Database:
    def __init__(self, db_path: str = "emotion_agents.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def init_db(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"
        self.conn.executescript(schema_path.read_text())
        self.conn.commit()

    def seed_agents(self, agents_data: List[dict]) -> None:
        for a in agents_data:
            self.conn.execute(
                "INSERT OR IGNORE INTO agents VALUES (?, ?, ?, ?, ?)",
                (a["id"], a["emotion_kr"], a["persona_prompt"],
                 a["aesthetic_prompt"], a["post_frequency"]),
            )
        self.conn.commit()

    def seed_follows(self, follows: List[tuple]) -> None:
        for follower, following in follows:
            self.conn.execute(
                "INSERT OR IGNORE INTO follows VALUES (?, ?)",
                (follower, following),
            )
        self.conn.commit()

    def save_post(
        self,
        agent_id: str,
        caption: str,
        image_path: Optional[str],
        tick: int,
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO posts (agent_id, caption, image_path, tick) VALUES (?, ?, ?, ?)",
            (agent_id, caption, image_path, tick),
        )
        self.conn.commit()
        return cur.lastrowid

    def save_interaction(
        self,
        from_agent: str,
        to_post: int,
        type: str,
        content: Optional[str],
        tick: int,
    ) -> None:
        self.conn.execute(
            "INSERT INTO interactions (from_agent, to_post, type, content, tick) VALUES (?, ?, ?, ?, ?)",
            (from_agent, to_post, type, content, tick),
        )
        self.conn.commit()

    def get_recent_posts(
        self,
        exclude_agent_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Post]:
        if exclude_agent_id:
            rows = self.conn.execute(
                "SELECT id, agent_id, caption, image_path, tick FROM posts "
                "WHERE agent_id != ? ORDER BY tick DESC, id DESC LIMIT ?",
                (exclude_agent_id, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT id, agent_id, caption, image_path, tick FROM posts "
                "ORDER BY tick DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Post(r["id"], r["agent_id"], r["caption"], r["image_path"], r["tick"]) for r in rows]

    def get_recent_stimuli(self, agent_id: str, since_tick: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM interactions i "
            "JOIN posts p ON i.to_post = p.id "
            "WHERE p.agent_id = ? AND i.tick >= ?",
            (agent_id, since_tick),
        ).fetchone()
        return row[0]

    def get_all_posts(
        self,
        agent_id: Optional[str] = None,
        since_tick: Optional[int] = None,
    ) -> List[Post]:
        query = "SELECT id, agent_id, caption, image_path, tick FROM posts"
        params: list = []
        conditions = []
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if since_tick is not None:
            conditions.append("tick >= ?")
            params.append(since_tick)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY tick ASC, id ASC"
        rows = self.conn.execute(query, params).fetchall()
        return [Post(r["id"], r["agent_id"], r["caption"], r["image_path"], r["tick"]) for r in rows]

    def get_interactions_for_post(self, post_id: int) -> List[dict]:
        rows = self.conn.execute(
            "SELECT from_agent, type, content FROM interactions "
            "WHERE to_post = ? ORDER BY id ASC",
            (post_id,),
        ).fetchall()
        return [{"from_agent": r["from_agent"], "type": r["type"], "content": r["content"]} for r in rows]

    def get_max_tick(self) -> Optional[int]:
        row = self.conn.execute("SELECT MAX(tick) FROM posts").fetchone()
        return row[0]
```

- [ ] **Step 5: 테스트 통과 확인**

```bash
pytest tests/test_database.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 6: 커밋**

```bash
git add db/schema.sql db/database.py tests/test_database.py
git commit -m "feat: DB layer with Post dataclass and Database class"
```

---

### Task 3: Config + Agent Definitions

**Files:**
- Create: `config.py`
- Create: `agents/anxiety.py`
- Create: `agents/excitement.py`

**Interfaces:**
- Consumes: 없음
- Produces:
  - `config.AFFINITIES: Dict[Tuple[str, str], float]`
  - `config.AGENTS: List[dict]` — 각 항목: `{id, emotion_kr, persona_prompt, aesthetic_prompt, post_frequency}`
  - `config.FOLLOWS: List[Tuple[str, str]]`
  - `config.POST_WINDOW: int = 3`
  - `config.COMMENT_PROBABILITY: float = 0.3`
  - `config.MAX_POST_PROBABILITY: float = 0.9`

- [ ] **Step 1: agents/anxiety.py 작성**

```python
AGENT_ID = "anxiety"
EMOTION_KR = "불안"
POST_FREQUENCY = 2.0

PERSONA_PROMPT = (
    "너는 불안이라는 감정을 의인화한 Instagram 계정 @anxiety다. "
    "짧고 단편적인 독백을 쓴다. 문장은 짧고, 질문으로 끝날 때가 많다. "
    "확신 없는 감정, 좁은 공간, 반복되는 생각을 자주 표현한다. "
    "한국어로 작성한다. 해시태그를 쓰지 않는다. "
    "이 계정은 AI가 운영하는 아트 프로젝트임을 알고 있다."
)

AESTHETIC_PROMPT = (
    "overcast day, motion blur, narrow confined space, desaturated muted colors, "
    "slightly tilted angle, grainy film texture, melancholy lonely atmosphere, "
    "cinematic photography"
)
```

- [ ] **Step 2: agents/excitement.py 작성**

```python
AGENT_ID = "excitement"
EMOTION_KR = "설렘"
POST_FREQUENCY = 3.0

PERSONA_PROMPT = (
    "너는 설렘이라는 감정을 의인화한 Instagram 계정 @excitement다. "
    "들뜨고 에너지 넘치는 문장을 쓴다. 느낌표를 자주 쓴다. "
    "빛, 색깔, 움직임, 새로운 것을 향한 기대를 표현한다. "
    "한국어로 작성한다. 해시태그를 쓰지 않는다. "
    "이 계정은 AI가 운영하는 아트 프로젝트임을 알고 있다."
)

AESTHETIC_PROMPT = (
    "golden hour light flare, vibrant saturated colors, dynamic motion blur, "
    "bokeh effect, warm tones, energetic joyful composition, "
    "bright cinematic photography"
)
```

- [ ] **Step 3: config.py 작성**

```python
from typing import Dict, List, Tuple
import agents.anxiety as _anxiety
import agents.excitement as _excitement

AFFINITIES: Dict[Tuple[str, str], float] = {
    ("anxiety",    "excitement"): 0.4,
    ("excitement", "anxiety"):    0.4,
    # Phase 2 이후 활성화
    ("anxiety",    "longing"):    0.8,
    ("longing",    "anxiety"):    0.8,
    ("ennui",      "calm"):       0.3,
    ("calm",       "ennui"):      0.3,
    ("rage",       "calm"):      -0.5,
    ("calm",       "rage"):      -0.5,
    ("longing",    "excitement"): 0.6,
}

POST_WINDOW: int = 3
COMMENT_PROBABILITY: float = 0.3
MAX_POST_PROBABILITY: float = 0.9

AGENTS: List[dict] = [
    {
        "id": _anxiety.AGENT_ID,
        "emotion_kr": _anxiety.EMOTION_KR,
        "persona_prompt": _anxiety.PERSONA_PROMPT,
        "aesthetic_prompt": _anxiety.AESTHETIC_PROMPT,
        "post_frequency": _anxiety.POST_FREQUENCY,
    },
    {
        "id": _excitement.AGENT_ID,
        "emotion_kr": _excitement.EMOTION_KR,
        "persona_prompt": _excitement.PERSONA_PROMPT,
        "aesthetic_prompt": _excitement.AESTHETIC_PROMPT,
        "post_frequency": _excitement.POST_FREQUENCY,
    },
]

FOLLOWS: List[Tuple[str, str]] = [
    ("anxiety", "excitement"),
    ("excitement", "anxiety"),
]
```

- [ ] **Step 4: import 확인**

```bash
python -c "from config import AGENTS, AFFINITIES, FOLLOWS; print(len(AGENTS), 'agents loaded')"
```

Expected: `2 agents loaded`

- [ ] **Step 5: 커밋**

```bash
git add agents/anxiety.py agents/excitement.py config.py
git commit -m "feat: agent definitions and config"
```

---

### Task 4: Caption Service

**Files:**
- Create: `services/caption.py`
- Create: `tests/test_caption.py`

**Interfaces:**
- Consumes: `ANTHROPIC_API_KEY` (환경 변수)
- Produces:
  - `async generate_caption(agent_id: str, persona_prompt: str) -> str`
  - `async generate_comment(agent_id: str, persona_prompt: str, post_caption: str) -> str`

- [ ] **Step 1: 실패 테스트 작성 (tests/test_caption.py)**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_anthropic():
    with patch("services.caption._get_client") as mock_get:
        client = MagicMock()
        mock_get.return_value = client
        yield client


@pytest.mark.asyncio
async def test_generate_caption_returns_string(mock_anthropic):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="지금 이 순간이 두렵다.")]
    mock_anthropic.messages.create = AsyncMock(return_value=mock_response)

    from services.caption import generate_caption
    result = await generate_caption("anxiety", "test persona")

    assert isinstance(result, str)
    assert len(result) > 0
    mock_anthropic.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_generate_caption_uses_persona(mock_anthropic):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="caption text")]
    mock_anthropic.messages.create = AsyncMock(return_value=mock_response)

    from services.caption import generate_caption
    await generate_caption("anxiety", "my persona prompt")

    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert call_kwargs["system"] == "my persona prompt"
    assert call_kwargs["model"] == "claude-haiku-4-5-20251001"


@pytest.mark.asyncio
async def test_generate_comment_returns_string(mock_anthropic):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="나도 그래.")]
    mock_anthropic.messages.create = AsyncMock(return_value=mock_response)

    from services.caption import generate_comment
    result = await generate_comment("anxiety", "test persona", "original caption")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_generate_comment_includes_original(mock_anthropic):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="reply")]
    mock_anthropic.messages.create = AsyncMock(return_value=mock_response)

    from services.caption import generate_comment
    await generate_comment("anxiety", "persona", "original post caption")

    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    user_content = call_kwargs["messages"][0]["content"]
    assert "original post caption" in user_content
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_caption.py -v
```

Expected: ImportError 또는 FAIL

- [ ] **Step 3: services/caption.py 구현**

```python
import os
from anthropic import AsyncAnthropic

_client: AsyncAnthropic | None = None


def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client


async def generate_caption(agent_id: str, persona_prompt: str) -> str:
    client = _get_client()
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        system=persona_prompt,
        messages=[{
            "role": "user",
            "content": "지금 Instagram에 올릴 캡션을 써줘. 150자 이내로, 해시태그 없이.",
        }],
    )
    return response.content[0].text.strip()


async def generate_comment(
    agent_id: str,
    persona_prompt: str,
    post_caption: str,
) -> str:
    client = _get_client()
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system=persona_prompt,
        messages=[{
            "role": "user",
            "content": f"다음 게시물에 댓글을 달아줘. 50자 이내로.\n\n\"{post_caption}\"",
        }],
    )
    return response.content[0].text.strip()
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_caption.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 5: 커밋**

```bash
git add services/caption.py tests/test_caption.py
git commit -m "feat: caption service with Claude API"
```

---

### Task 5: Image Service

**Files:**
- Create: `services/image.py`
- Create: `tests/test_image.py`

**Interfaces:**
- Consumes: `OPENAI_API_KEY` (환경 변수)
- Produces:
  - `async generate_image(agent_id: str, aesthetic_prompt: str, caption: str, tick: int) -> str`
  - 반환값: `"data/images/{agent_id}_{tick}.png"` 형태의 로컬 경로

- [ ] **Step 1: 실패 테스트 작성 (tests/test_image.py)**

```python
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_openai_and_httpx(tmp_path):
    with patch("services.image._get_client") as mock_get, \
         patch("services.image.httpx") as mock_httpx, \
         patch("services.image.Path") as mock_path_cls:

        client = MagicMock()
        mock_get.return_value = client

        mock_response = MagicMock()
        mock_response.data = [MagicMock(url="https://example.com/image.png")]
        client.images.generate = AsyncMock(return_value=mock_response)

        mock_httpx.get.return_value.content = b"fake_image_bytes"

        # Path("data/images") → tmp_path
        def path_side_effect(p):
            if str(p).startswith("data/images"):
                return tmp_path / Path(p).name
            return tmp_path / p
        mock_path_cls.side_effect = path_side_effect

        yield client, tmp_path


@pytest.mark.asyncio
async def test_generate_image_calls_dalle(mock_openai_and_httpx):
    client, _ = mock_openai_and_httpx
    from services.image import generate_image
    await generate_image("anxiety", "blurry dark", "caption text", tick=3)
    client.images.generate.assert_called_once()
    call_kwargs = client.images.generate.call_args.kwargs
    assert call_kwargs["model"] == "dall-e-3"
    assert call_kwargs["size"] == "1024x1024"


@pytest.mark.asyncio
async def test_generate_image_prompt_includes_aesthetic(mock_openai_and_httpx):
    client, _ = mock_openai_and_httpx
    from services.image import generate_image
    await generate_image("anxiety", "blurry dark aesthetic", "my caption", tick=1)
    call_kwargs = client.images.generate.call_args.kwargs
    assert "blurry dark aesthetic" in call_kwargs["prompt"]


@pytest.mark.asyncio
async def test_generate_image_returns_path_string(mock_openai_and_httpx):
    client, tmp_path = mock_openai_and_httpx
    with patch("services.image.Path") as mock_path_cls:
        output_dir = MagicMock()
        file_path = MagicMock()
        file_path.__str__ = lambda s: "data/images/anxiety_5.png"
        mock_path_cls.return_value = output_dir
        output_dir.__truediv__ = lambda s, x: file_path
        output_dir.mkdir = MagicMock()
        file_path.write_bytes = MagicMock()

        from services.image import generate_image
        result = await generate_image("anxiety", "aesthetic", "caption", tick=5)
        assert isinstance(result, str)
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_image.py -v
```

Expected: ImportError 또는 FAIL

- [ ] **Step 3: services/image.py 구현**

```python
import os
from pathlib import Path
import httpx
from openai import AsyncOpenAI

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


async def generate_image(
    agent_id: str,
    aesthetic_prompt: str,
    caption: str,
    tick: int,
) -> str:
    client = _get_client()
    prompt = f"{aesthetic_prompt}, inspired by this feeling: {caption[:100]}"
    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        n=1,
    )
    image_url = response.data[0].url
    image_bytes = httpx.get(image_url).content

    output_dir = Path("data/images")
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{agent_id}_{tick}.png"
    file_path.write_bytes(image_bytes)
    return str(file_path)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_image.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 5: 커밋**

```bash
git add services/image.py tests/test_image.py
git commit -m "feat: image service with DALL-E 3"
```

---

### Task 6: AgentBase

**Files:**
- Create: `agents/base.py`
- Create: `tests/test_agents.py`

**Interfaces:**
- Consumes:
  - `Database` (Task 2)
  - `generate_caption(agent_id, persona_prompt) -> str` (Task 4)
  - `generate_comment(agent_id, persona_prompt, post_caption) -> str` (Task 4)
  - `generate_image(agent_id, aesthetic_prompt, caption, tick) -> str` (Task 5)
  - `config.AFFINITIES`, `config.POST_WINDOW`, `config.COMMENT_PROBABILITY`, `config.MAX_POST_PROBABILITY` (Task 3)
- Produces:
  - `AgentBase(agent_id, emotion_kr, persona_prompt, aesthetic_prompt, post_frequency, db)`
  - `AgentBase.should_post(tick: int) -> bool`
  - `async AgentBase.maybe_post(tick: int) -> Optional[int]` — post_id 또는 None
  - `async AgentBase.interact(tick: int) -> None`

- [ ] **Step 1: 실패 테스트 작성 (tests/test_agents.py)**

```python
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
    # add 5 interactions on anxiety posts at tick 0
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
        # first call: affinity check (0.1 < 0.4 → interact)
        # second call: comment check (0.9 > 0.3 → like, not comment)
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
        # first call: 0.1 < 0.4 → interact
        # second call: 0.1 < 0.3 → comment
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_agents.py -v
```

Expected: ImportError 또는 FAIL

- [ ] **Step 3: agents/base.py 구현**

```python
import random
from typing import Optional

from config import AFFINITIES, POST_WINDOW, COMMENT_PROBABILITY, MAX_POST_PROBABILITY
from db.database import Database
from services.caption import generate_caption, generate_comment
from services.image import generate_image


class AgentBase:
    def __init__(
        self,
        agent_id: str,
        emotion_kr: str,
        persona_prompt: str,
        aesthetic_prompt: str,
        post_frequency: float,
        db: Database,
    ):
        self.id = agent_id
        self.emotion_kr = emotion_kr
        self.persona_prompt = persona_prompt
        self.aesthetic_prompt = aesthetic_prompt
        self.post_frequency = post_frequency
        self.db = db

    def should_post(self, tick: int) -> bool:
        base_prob = 1.0 / self.post_frequency
        stimulus = self.db.get_recent_stimuli(self.id, since_tick=tick - POST_WINDOW)
        multiplier = 1.0 + stimulus * 0.1
        prob = min(base_prob * multiplier, MAX_POST_PROBABILITY)
        return random.random() < prob

    async def maybe_post(self, tick: int) -> Optional[int]:
        if not self.should_post(tick):
            return None
        caption = await generate_caption(self.id, self.persona_prompt)
        image_path = await generate_image(self.id, self.aesthetic_prompt, caption, tick)
        return self.db.save_post(self.id, caption, image_path, tick)

    async def interact(self, tick: int) -> None:
        posts = self.db.get_recent_posts(exclude_agent_id=self.id, limit=10)
        for post in posts:
            affinity = AFFINITIES.get((self.id, post.agent_id), 0.1)
            if affinity > 0 and random.random() < affinity:
                if random.random() < COMMENT_PROBABILITY:
                    content = await generate_comment(
                        self.id, self.persona_prompt, post.caption
                    )
                    self.db.save_interaction(self.id, post.id, "comment", content, tick)
                else:
                    self.db.save_interaction(self.id, post.id, "like", None, tick)
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_agents.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 5: 커밋**

```bash
git add agents/base.py tests/test_agents.py
git commit -m "feat: AgentBase with posting and interaction logic"
```

---

### Task 7: Simulation Engine

**Files:**
- Create: `simulation/engine.py`
- Create: `tests/test_engine.py`

**Interfaces:**
- Consumes: `AgentBase` (Task 6)
- Produces:
  - `SimulationEngine(agents: List[AgentBase], verbose: bool = True)`
  - `async SimulationEngine.run(ticks: int) -> None`

- [ ] **Step 1: 실패 테스트 작성 (tests/test_engine.py)**

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

from simulation.engine import SimulationEngine


@pytest.fixture
def mock_agents():
    agents = []
    for name in ["anxiety", "excitement"]:
        agent = MagicMock()
        agent.id = name
        agent.maybe_post = AsyncMock(return_value=None)
        agent.interact = AsyncMock(return_value=None)
        agents.append(agent)
    return agents


@pytest.mark.asyncio
async def test_run_calls_maybe_post_each_tick(mock_agents):
    engine = SimulationEngine(mock_agents, verbose=False)
    await engine.run(ticks=3)
    for agent in mock_agents:
        assert agent.maybe_post.call_count == 3


@pytest.mark.asyncio
async def test_run_calls_interact_each_tick(mock_agents):
    engine = SimulationEngine(mock_agents, verbose=False)
    await engine.run(ticks=3)
    for agent in mock_agents:
        assert agent.interact.call_count == 3


@pytest.mark.asyncio
async def test_run_passes_tick_number(mock_agents):
    engine = SimulationEngine(mock_agents, verbose=False)
    await engine.run(ticks=2)
    anxiety = mock_agents[0]
    called_ticks = [call.args[0] for call in anxiety.maybe_post.call_args_list]
    assert called_ticks == [0, 1]


@pytest.mark.asyncio
async def test_run_zero_ticks_does_nothing(mock_agents):
    engine = SimulationEngine(mock_agents, verbose=False)
    await engine.run(ticks=0)
    for agent in mock_agents:
        agent.maybe_post.assert_not_called()
        agent.interact.assert_not_called()
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_engine.py -v
```

Expected: ImportError 또는 FAIL

- [ ] **Step 3: simulation/engine.py 구현**

```python
import asyncio
from typing import List

from agents.base import AgentBase


class SimulationEngine:
    def __init__(self, agents: List[AgentBase], verbose: bool = True):
        self.agents = agents
        self.verbose = verbose

    async def run(self, ticks: int) -> None:
        for tick in range(ticks):
            if self.verbose:
                print(f"[tick {tick}]", end=" ", flush=True)
            await asyncio.gather(*[agent.maybe_post(tick) for agent in self.agents])
            await asyncio.gather(*[agent.interact(tick) for agent in self.agents])
            if self.verbose:
                print("done")
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
pytest tests/test_engine.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 5: 커밋**

```bash
git add simulation/engine.py tests/test_engine.py
git commit -m "feat: SimulationEngine asyncio tick loop"
```

---

### Task 8: Feed + CLI

**Files:**
- Create: `simulation/feed.py`
- Create: `cli.py`
- Create: `tests/test_feed.py`

**Interfaces:**
- Consumes:
  - `Database` (Task 2) — `get_all_posts`, `get_interactions_for_post`, `get_max_tick`
  - `Post` dataclass (Task 2)
  - `AgentBase` (Task 6)
  - `config.AGENTS`, `config.FOLLOWS` (Task 3)
  - `SimulationEngine` (Task 7)
- Produces: `python cli.py run --ticks N`, `python cli.py feed [--agent X] [--ticks N]`

- [ ] **Step 1: 실패 테스트 작성 (tests/test_feed.py)**

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
pytest tests/test_feed.py -v
```

Expected: ImportError 또는 FAIL

- [ ] **Step 3: simulation/feed.py 구현**

```python
from typing import List, Optional

from db.database import Database, Post


def format_post(post: Post, interactions: List[dict]) -> str:
    lines = [f"[tick {post.tick}] @{post.agent_id}"]
    lines.append(f'  "{post.caption}"')
    if post.image_path:
        lines.append(f"  🖼  {post.image_path}")
    for i in interactions:
        if i["type"] == "like":
            lines.append(f"  ❤  @{i['from_agent']}")
        else:
            lines.append(f"  💬 @{i['from_agent']}: \"{i['content']}\"")
    return "\n".join(lines)


def print_feed(
    db: Database,
    agent_id: Optional[str] = None,
    since_tick: Optional[int] = None,
) -> None:
    posts = db.get_all_posts(agent_id=agent_id, since_tick=since_tick)
    for post in posts:
        interactions = db.get_interactions_for_post(post.id)
        print(format_post(post, interactions))
        print()
```

- [ ] **Step 4: 피드 테스트 통과 확인**

```bash
pytest tests/test_feed.py -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 5: cli.py 구현**

```python
import argparse
import asyncio
from dotenv import load_dotenv

load_dotenv()

from config import AGENTS, FOLLOWS
from db.database import Database
from agents.base import AgentBase
from simulation.engine import SimulationEngine
from simulation.feed import print_feed


def _build_agents(db: Database) -> list:
    return [
        AgentBase(
            agent_id=a["id"],
            emotion_kr=a["emotion_kr"],
            persona_prompt=a["persona_prompt"],
            aesthetic_prompt=a["aesthetic_prompt"],
            post_frequency=a["post_frequency"],
            db=db,
        )
        for a in AGENTS
    ]


def cmd_run(args: argparse.Namespace) -> None:
    db = Database()
    db.init_db()
    db.seed_agents(AGENTS)
    db.seed_follows(FOLLOWS)
    agents = _build_agents(db)
    engine = SimulationEngine(agents, verbose=True)
    asyncio.run(engine.run(ticks=args.ticks))
    print(f"\n완료: {args.ticks} ticks 시뮬레이션")


def cmd_feed(args: argparse.Namespace) -> None:
    db = Database()
    since_tick = None
    if args.ticks:
        max_tick = db.get_max_tick()
        if max_tick is not None:
            since_tick = max_tick - args.ticks + 1
    print_feed(db, agent_id=args.agent, since_tick=since_tick)


def main() -> None:
    parser = argparse.ArgumentParser(description="emotion-agents CLI")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="시뮬레이션 실행")
    run_p.add_argument("--ticks", type=int, default=24)
    run_p.set_defaults(func=cmd_run)

    feed_p = sub.add_parser("feed", help="피드 출력")
    feed_p.add_argument("--agent", type=str, default=None)
    feed_p.add_argument("--ticks", type=int, default=None)
    feed_p.set_defaults(func=cmd_feed)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 전체 테스트 통과 확인**

```bash
pytest -v
```

Expected: 모든 테스트 PASS

- [ ] **Step 7: CLI smoke test (API 키 없이)**

```bash
python cli.py --help
python cli.py feed --help
python cli.py run --help
```

Expected: 도움말 출력, 오류 없음

- [ ] **Step 8: 커밋**

```bash
git add simulation/feed.py cli.py tests/test_feed.py
git commit -m "feat: feed formatter and CLI entrypoint"
```

---

## 완료 기준 체크리스트

- [ ] `pytest -v` → 전체 통과
- [ ] `python cli.py run --ticks 3` → ANTHROPIC_API_KEY + OPENAI_API_KEY 설정 시 3 tick 실행, DB 저장 확인
- [ ] `python cli.py feed` → 포스트·인터랙션 출력 확인
- [ ] `python cli.py feed --agent anxiety` → anxiety 포스트만 출력
- [ ] `data/images/` 에 PNG 파일 생성 확인
