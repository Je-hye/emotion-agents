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


@pytest.mark.asyncio
async def test_generate_caption_includes_disclosure(mock_anthropic):
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="지금 이 순간이 두렵다.")]
    mock_anthropic.messages.create = AsyncMock(return_value=mock_response)

    from services.caption import generate_caption
    result = await generate_caption("anxiety", "persona")
    assert result.endswith("\n\n이 게시물은 AI 아트 프로젝트(@emotion_agents)가 생성했습니다.")
