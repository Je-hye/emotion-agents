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
