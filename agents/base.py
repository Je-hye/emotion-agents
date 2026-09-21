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
