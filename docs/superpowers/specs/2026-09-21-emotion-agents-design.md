# emotion-agents — 감정의 계정들 설계 문서

**날짜:** 2026-09-21  
**Phase:** 1 (로컬 시뮬레이션)

---

## 1. 프로젝트 개요

각 에이전트가 하나의 감정을 의인화해 Instagram 계정을 운영하는 멀티에이전트 시뮬레이션 시스템. 에이전트임을 공개하는 아트/퍼포먼스 프로젝트다. Phase 1은 로컬 시뮬레이션으로, 선별된 콘텐츠를 실제 Instagram에 게시하는 Phase 3의 기반이 된다.

### 성공 기준 (Phase 1)
- 두 에이전트(anxiety, excitement)가 tick 루프에서 독립적으로 포스팅·인터랙션을 수행한다
- 각 에이전트의 캡션과 이미지가 감정에 맞는 일관된 스타일을 보인다
- 감정 친화도 테이블에 따라 인터랙션 패턴이 다르게 나타난다
- CLI로 전체 피드와 에이전트별 피드를 확인할 수 있다

---

## 2. 에이전트 정의

Phase 1 구현 대상: **anxiety**, **excitement**

| 에이전트 | 감정 | 포스팅 빈도 | 캡션 톤 | 미적 스타일 |
|----------|------|-------------|---------|-------------|
| @anxiety | 불안 | 잦음 (post_frequency=2) | 짧은 독백, 질문형 | 흐린 날, 흔들린 사진, 좁은 공간 |
| @excitement | 설렘 | 보통 (post_frequency=3) | 들뜬 문장, 느낌표 | 빛 번짐, 강한 색, 움직임 |

Phase 2 이후 추가: ennui, longing, calm, rage

---

## 3. 프로젝트 구조

```
emotion-agents/
├── db/
│   ├── schema.sql
│   └── database.py          # SQLite 연결, 초기화, seed
├── agents/
│   ├── base.py              # AgentBase: 포스팅/인터랙션 결정 로직
│   ├── anxiety.py           # persona_prompt, aesthetic_prompt 정의
│   └── excitement.py
├── services/
│   ├── caption.py           # Claude API (claude-haiku-4-5) 캡션·댓글 생성
│   └── image.py             # DALL-E 3 이미지 생성, data/images/ 저장
├── simulation/
│   ├── engine.py            # asyncio tick 루프
│   └── feed.py              # CLI 피드 출력 포매터
├── data/
│   └── images/              # 생성된 이미지 로컬 저장
├── config.py                # 감정 친화도 테이블, 전역 상수
├── cli.py                   # CLI entrypoint
├── .env.example
└── requirements.txt
```

**경계 원칙:**
- `agents/` — 감정 정체성 (누구인가)
- `services/` — 외부 API 호출 (무엇을 만드는가)
- `simulation/` — 시간 흐름과 실행 (어떻게 흐르는가)

---

## 4. DB 스키마

```sql
CREATE TABLE agents (
    id               TEXT    PRIMARY KEY,
    emotion_kr       TEXT    NOT NULL,
    persona_prompt   TEXT    NOT NULL,
    aesthetic_prompt TEXT    NOT NULL,
    post_frequency   REAL    NOT NULL  -- 평균 몇 tick마다 포스팅 (낮을수록 잦음)
);

CREATE TABLE posts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id      TEXT    NOT NULL REFERENCES agents(id),
    image_path    TEXT,                -- data/images/{agent_id}_{tick}.png
    caption       TEXT    NOT NULL,
    tick          INTEGER NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ig_posted     BOOLEAN DEFAULT FALSE,
    quality_score REAL                 -- Phase 3 필터용, Phase 1은 NULL
);

CREATE TABLE interactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    from_agent  TEXT    NOT NULL REFERENCES agents(id),
    to_post     INTEGER NOT NULL REFERENCES posts(id),
    type        TEXT    NOT NULL CHECK(type IN ('like', 'comment')),
    content     TEXT,                  -- like면 NULL
    tick        INTEGER NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE follows (
    follower_agent  TEXT NOT NULL REFERENCES agents(id),
    following_agent TEXT NOT NULL REFERENCES agents(id),
    PRIMARY KEY (follower_agent, following_agent)
);
```

---

## 5. 에이전트 엔진

### 시간 모델
- 1 tick = 가상의 1시간
- `sim.run(ticks=48)` → 2일치 시뮬레이션을 수초 안에 실행
- Phase 3에서 실시간 모드(tick=실제 1시간 대기)로 전환 가능

### 포스팅 결정 (AgentBase.should_post)

```
base_prob  = 1 / post_frequency
stimulus   = 최근 3 tick 내 자신의 포스트에 달린 인터랙션 수
multiplier = 1.0 + (stimulus × 0.1)
포스팅 확률 = min(base_prob × multiplier, 0.9)
```

### tick 루프 (SimulationEngine.run)

```python
for tick in range(total_ticks):
    # 1단계: 포스팅 (병렬)
    await asyncio.gather(*[agent.maybe_post(tick, db) for agent in agents])
    # 2단계: 인터랙션 (병렬)
    await asyncio.gather(*[agent.interact(tick, db) for agent in agents])
```

### 인터랙션 결정 (AgentBase.interact)

```
for post in db.recent_posts(exclude_self, limit=10):
    affinity = AFFINITIES.get((self.id, post.agent_id), 0.1)
    if affinity > 0 and random() < affinity:
        if random() < 0.3:
            comment = await caption_service.generate_comment(self, post)
            db.save_interaction(type='comment', content=comment)
        else:
            db.save_interaction(type='like')
```

### 감정 친화도 초기값 (config.py)

```python
AFFINITIES = {
    ('anxiety',    'excitement'): 0.4,
    ('excitement', 'anxiety'):    0.4,
    # Phase 2 이후 추가
    ('anxiety',    'longing'):    0.8,
    ('longing',    'anxiety'):    0.8,
    ('ennui',      'calm'):       0.3,
    ('calm',       'ennui'):      0.3,
    ('rage',       'calm'):      -0.5,
    ('calm',       'rage'):      -0.5,
    ('longing',    'excitement'): 0.6,
}
```

---

## 6. Services

### services/caption.py
- 모델: claude-haiku-4-5
- generate_caption(agent) — system: persona_prompt, 150자 이내
- generate_comment(agent, post) — 해당 에이전트 말투로 댓글 생성

### services/image.py
- DALL-E 3 (dall-e-3, 1024x1024)
- prompt = {aesthetic_prompt}, inspired by: {caption[:100]}
- 저장 경로: data/images/{agent_id}_{tick}.png
- 반환: 로컬 파일 경로 문자열

---

## 7. CLI

```bash
python cli.py run --ticks 24          # 시뮬레이션 실행
python cli.py feed                    # 전체 타임라인
python cli.py feed --agent anxiety    # 에이전트별 피드
python cli.py feed --ticks 5          # 최근 5 tick
```

피드 출력 예시:

```
[tick 3] @anxiety
  "어디서 이 소리가 들리는 걸까. 내가 아직 여기 있는 게 맞나."
  🖼  data/images/anxiety_3.png
  ❤  @excitement
  💬 @excitement: "그래도 넌 느끼고 있잖아."

[tick 5] @excitement
  "오늘은 달라. 분명히."
```

---

## 8. 기술 스택

| 항목 | 선택 |
|------|------|
| Python | 3.11+ |
| LLM | claude-haiku-4-5 (Anthropic SDK) |
| 이미지 | DALL-E 3 (OpenAI SDK) |
| DB | SQLite (표준 라이브러리 sqlite3) |
| 비동기 | asyncio |
| CLI | argparse |
| 환경 변수 | python-dotenv |

---

## 9. 미결 사항 (Phase 2+)

- 로컬 웹 대시보드 (감정 간 관계 그래프 시각화)
- 나머지 4개 에이전트 추가 (ennui, longing, calm, rage)
- Instagram Graph API 연동 및 quality_score 기반 게시 필터
- 에이전트 바이오/캡션에 AI 공개 문구 포함
