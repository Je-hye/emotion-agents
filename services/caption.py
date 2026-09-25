import os
from anthropic import AsyncAnthropic

_client: AsyncAnthropic | None = None

DISCLOSURE = "\n\n이 게시물은 AI 아트 프로젝트(@emotion_agents)가 생성했습니다."


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
    return response.content[0].text.strip() + DISCLOSURE


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
