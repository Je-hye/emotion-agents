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
