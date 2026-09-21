# emotion-agents Phase 2 — 에이전트 확장 + Instagram 스타일 UI 설계 문서

**날짜:** 2026-09-22
**Phase:** 2 (에이전트 확장 + 로컬 웹 UI)

---

## 1. 개요

Phase 1(로컬 CLI 시뮬레이션) 위에 두 레이어를 추가한다.

1. **에이전트 확장** — ennui, longing, calm, rage 4개 추가 (6개 에이전트)
2. **FastAPI REST API** — 기존 SQLite DB를 HTTP로 노출
3. **React SPA** — Instagram 스타일 UI (타임라인, 프로필 그리드, 관계 그래프)
4. **quality_score 큐레이션** — UI 슬라이더로 포스트 점수 부여

시뮬레이션은 기존 `cli.py run`으로 실행하고, UI는 결과 탐색·큐레이션 전용으로 역할을 분리한다.

### 성공 기준
- 6개 에이전트 시뮬레이션 후 각 에이전트 프로필과 타임라인이 UI에 표시된다
- quality_score 슬라이더 조작이 DB에 즉시 반영된다
- 관계 그래프에서 affinity 강도가 엣지 굵기로 표현된다
- `pytest -v` 전체 통과, `npm run test` 프론트엔드 테스트 통과

---

## 2. 에이전트 정의

### 신규 에이전트 (4개)

| 에이전트 | 감정 | post_frequency | 캡션 톤 | 미적 스타일 |
|----------|------|----------------|---------|-------------|
| @ennui | 권태 | 5.0 | 무감각한 독백, 평서문 | 회색빛 실내, 흐린 창문, 반복되는 패턴 |
| @longing | 그리움 | 3.0 | 부재에 대한 서술, 과거 시제 | 빈 자리, 역광, 흐릿한 인물 실루엣 |
| @calm | 평온 | 4.0 | 짧고 여백 있는 문장, 현재 시제 | 자연광, 미니멀, 넓은 여백 |
| @rage | 분노 | 1.5 | 단편적·폭발적, 대문자 없음 | 강렬한 대비, 클로즈업, 붉은 계열 |

### AFFINITIES 업데이트 (Phase 2 항목 활성화)

```python
("anxiety",   "longing"):    0.8,
("longing",   "anxiety"):    0.8,
("ennui",     "calm"):       0.3,
("calm",      "ennui"):      0.3,
("rage",      "calm"):      -0.5,   # 인터랙션 없음 (affinity > 0 조건)
("calm",      "rage"):      -0.5,
("longing",   "excitement"): 0.6,
```

FOLLOWS: 전체 6개 에이전트 상호 팔로우 (affinity > 0인 쌍만)

---

## 3. 프로젝트 구조

```
emotion-agents/
├── (Phase 1 그대로)
│
├── api/
│   ├── __init__.py
│   ├── main.py             # FastAPI app, StaticFiles, CORS
│   └── routes/
│       ├── __init__.py
│       ├── posts.py        # GET /api/posts, GET /api/posts/{id}, PATCH /api/posts/{id}/score
│       ├── agents.py       # GET /api/agents
│       └── graph.py        # GET /api/graph, GET /api/stats
│
└── web/
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/client.ts       # axios 인스턴스
    │   ├── pages/
    │   │   ├── Feed.tsx        # / — 타임라인
    │   │   ├── Profile.tsx     # /@:agent_id — 그리드 프로필
    │   │   └── Graph.tsx       # /graph — 관계 그래프
    │   └── components/
    │       ├── PostCard.tsx
    │       ├── PostModal.tsx
    │       ├── QualitySlider.tsx
    │       └── RelationGraph.tsx
    ├── package.json
    ├── tsconfig.json
    └── vite.config.ts
```

---

## 4. API 설계

### 엔드포인트

```
GET  /api/agents
GET  /api/posts?agent_id=&since_tick=&min_score=
GET  /api/posts/{post_id}
PATCH /api/posts/{post_id}/score        body: {"score": 0.85}
GET  /api/graph
GET  /api/stats
```

### 응답 구조

```json
// GET /api/agents
[{"id": "anxiety", "emotion_kr": "불안", "post_frequency": 2.0}]

// GET /api/posts
[{
  "id": 1,
  "agent_id": "anxiety",
  "caption": "...",
  "image_url": "/data/images/anxiety_3.png",
  "tick": 3,
  "quality_score": null,
  "interactions": [{"from_agent": "excitement", "type": "like", "content": null}]
}]

// GET /api/graph
{
  "nodes": [{"id": "anxiety", "emotion_kr": "불안", "post_count": 12}],
  "edges": [{"source": "anxiety", "target": "excitement", "affinity": 0.4}]
}

// GET /api/stats
{"anxiety": {"post_count": 12, "received_likes": 5, "received_comments": 2}}
```

`data/images/`는 FastAPI `StaticFiles`로 `/data/images/` 경로에 마운트.
기존 `Database` 클래스 싱글톤으로 주입 (`Depends`).

---

## 5. React UI

### 기술 스택
- Vite + TypeScript + TailwindCSS
- React Router v6
- react-force-graph-2d (관계 그래프)
- axios (API 호출)
- Vitest + React Testing Library (테스트)

### 화면

**① `/` — 타임라인 피드**
- 전체 포스트 tick 역순, 상단 필터바 (에이전트·tick 범위·미큐레이션 토글)
- PostCard: 이미지 + 캡션 + 인터랙션 + QualitySlider
- 슬라이더 변경 → `PATCH /api/posts/{id}/score` 즉시 호출

**② `/@:agent_id` — 에이전트 프로필**
- 헤더: 에이전트명·감정·포스트 수·인터랙션 통계
- 3열 그리드 (Instagram 스타일), 썸네일 클릭 → PostModal
- quality_score 기준 정렬 토글

**③ `/graph` — 관계 그래프**
- 노드: 에이전트 (크기 = 포스트 수)
- 엣지: affinity 값 (굵기 = 강도, 빨강 = 음수 rage↔calm)
- 노드 클릭 → `/@:agent_id`로 이동

### 개발 환경

```bash
# vite.config.ts proxy
server: { proxy: { '/api': 'http://localhost:8000', '/data': 'http://localhost:8000' } }
```

---

## 6. 테스트 전략

**백엔드**
- `tests/test_api.py`: FastAPI `TestClient` + `:memory:` DB
  - 각 엔드포인트 응답 구조 검증
  - `PATCH /score` 저장 확인
  - 필터 파라미터 동작 검증

**프론트엔드**
- `web/src/__tests__/PostCard.test.tsx`: 캡션·이미지·인터랙션 렌더링
- `web/src/__tests__/QualitySlider.test.tsx`: 슬라이더 변경 → API 호출 mock 확인
- `web/src/__tests__/RelationGraph.test.tsx`: 노드/엣지 smoke test

**통합 smoke test**
```bash
python cli.py run --ticks 3
uvicorn api.main:app &
curl localhost:8000/api/posts
```

---

## 7. 실행 방법

```bash
# 시뮬레이션 (터미널 1)
python cli.py run --ticks 24

# API 서버 (터미널 2)
uvicorn api.main:app --reload

# React 개발 서버 (터미널 3)
cd web && npm run dev
```

프로덕션: `npm run build` → `web/dist/`를 FastAPI StaticFiles로 서빙, 단일 포트.

---

## 8. 미결 사항 (Phase 3)

- Instagram Graph API 연동 (quality_score 기반 게시 필터 포함)
- 에이전트 바이오/캡션에 AI 공개 문구
- 실시간 tick 스트리밍 (WebSocket)
