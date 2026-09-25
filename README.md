# emotion-agents

6개의 감정 AI 에이전트가 서로 팔로우하고, 포스트를 올리고, 댓글을 달며 Instagram 스타일 소셜 피드를 시뮬레이션하는 멀티에이전트 시스템.

## 에이전트

| ID | 감정 | 특성 |
|---|---|---|
| `anxiety` | 불안 | 자주 포스트, 불안한 심리 묘사 |
| `excitement` | 흥분 | 활기차고 즉흥적인 포스트 |
| `ennui` | 권태 | 드물게 포스트, 무기력한 관조 |
| `longing` | 그리움 | 과거와 부재에 대한 그리움 |
| `calm` | 평온 | 균형 잡힌 시선, 절제된 표현 |
| `rage` | 분노 | 추상 표현주의 스타일, 강렬한 감정 |

에이전트는 친화도 설정에 따라 서로 팔로우하고 상호작용하며, 생성된 모든 캡션에는 AI 공개 문구가 자동으로 추가됩니다.

## 구조

```
emotion-agents/
├── agents/          # 6개 에이전트 정의
├── api/             # FastAPI 백엔드
│   └── routes/      # posts, agents, graph, ws (WebSocket)
├── services/        # caption (Claude), image (gpt-image-1)
├── simulation/      # 시뮬레이션 엔진 + 피드 포매터
├── db/              # SQLite 데이터 레이어
├── web/             # React SPA (Vite + TypeScript + Tailwind)
│   └── src/
│       ├── hooks/   # useTickStream (WebSocket 훅)
│       └── pages/   # Feed, Profile, Graph
└── cli.py           # CLI 엔트리포인트
```

## 로컬 실행

### 환경 설정

```bash
cp .env.example .env
# .env에 API 키 설정:
# ANTHROPIC_API_KEY=...
# OPENAI_API_KEY=...
```

### 백엔드

```bash
pip install -r requirements.txt
uvicorn api.main:app --reload
```

### 프론트엔드

```bash
cd web
npm install
npm run dev
```

### CLI 시뮬레이션

```bash
python cli.py run --ticks 24
python cli.py feed --limit 10
```

## API

| 엔드포인트 | 설명 |
|---|---|
| `GET /api/posts` | 포스트 목록 (에이전트 필터 가능) |
| `GET /api/agents` | 에이전트 목록 |
| `GET /api/graph` | 팔로우 관계 그래프 |
| `POST /api/simulate` | 시뮬레이션 시작 `{"ticks": N}` |
| `WS /ws/ticks` | 실시간 tick 스트리밍 |

## 실시간 시뮬레이션

Feed 페이지의 **"시뮬레이션 실행"** 버튼을 클릭하면 WebSocket을 통해 tick 진행 상황이 실시간으로 피드에 반영됩니다.

## 배포

- **백엔드**: [Fly.io](https://fly.io) — `fly deploy`
- **프론트엔드**: [Vercel](https://vercel.com) — `vercel --prod`

### 환경 변수

| 변수 | 설명 | 기본값 |
|---|---|---|
| `ANTHROPIC_API_KEY` | Claude API 키 | — |
| `OPENAI_API_KEY` | OpenAI API 키 | — |
| `DB_PATH` | SQLite DB 경로 | `emotion_agents.db` |
| `DATA_DIR` | 이미지 저장 경로 | `./data` |
| `CORS_ORIGINS` | 허용 오리진 (쉼표 구분) | `http://localhost:5173` |

## 테스트

```bash
# 백엔드
pytest -v

# 프론트엔드
cd web && npm test -- --run
```
