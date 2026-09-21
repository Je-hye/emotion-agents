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
