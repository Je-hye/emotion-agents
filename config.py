from typing import Dict, List, Tuple
import agents.anxiety as _anxiety
import agents.excitement as _excitement
import agents.ennui as _ennui
import agents.longing as _longing
import agents.calm as _calm
import agents.rage as _rage

AFFINITIES: Dict[Tuple[str, str], float] = {
    ("anxiety",    "excitement"): 0.4,
    ("excitement", "anxiety"):    0.4,
    ("anxiety",    "longing"):    0.8,
    ("longing",    "anxiety"):    0.8,
    ("ennui",      "calm"):       0.3,
    ("calm",       "ennui"):      0.3,
    ("rage",       "calm"):      -0.5,
    ("calm",       "rage"):      -0.5,
    ("longing",    "excitement"): 0.6,
    ("excitement", "longing"):    0.6,
}

POST_WINDOW: int = 3
COMMENT_PROBABILITY: float = 0.3
MAX_POST_PROBABILITY: float = 0.9

def _agent_dict(mod) -> dict:
    return {
        "id": mod.AGENT_ID,
        "emotion_kr": mod.EMOTION_KR,
        "persona_prompt": mod.PERSONA_PROMPT,
        "aesthetic_prompt": mod.AESTHETIC_PROMPT,
        "post_frequency": mod.POST_FREQUENCY,
    }

AGENTS: List[dict] = [
    _agent_dict(_anxiety),
    _agent_dict(_excitement),
    _agent_dict(_ennui),
    _agent_dict(_longing),
    _agent_dict(_calm),
    _agent_dict(_rage),
]

FOLLOWS: List[Tuple[str, str]] = [
    ("anxiety",    "excitement"),
    ("excitement", "anxiety"),
    ("anxiety",    "longing"),
    ("longing",    "anxiety"),
    ("ennui",      "calm"),
    ("calm",       "ennui"),
    ("longing",    "excitement"),
    ("excitement", "longing"),
]
