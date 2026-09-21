import pytest
from unittest.mock import AsyncMock, MagicMock

from simulation.engine import SimulationEngine


@pytest.fixture
def mock_agents():
    agents = []
    for name in ["anxiety", "excitement"]:
        agent = MagicMock()
        agent.id = name
        agent.maybe_post = AsyncMock(return_value=None)
        agent.interact = AsyncMock(return_value=None)
        agents.append(agent)
    return agents


@pytest.mark.asyncio
async def test_run_calls_maybe_post_each_tick(mock_agents):
    engine = SimulationEngine(mock_agents, verbose=False)
    await engine.run(ticks=3)
    for agent in mock_agents:
        assert agent.maybe_post.call_count == 3


@pytest.mark.asyncio
async def test_run_calls_interact_each_tick(mock_agents):
    engine = SimulationEngine(mock_agents, verbose=False)
    await engine.run(ticks=3)
    for agent in mock_agents:
        assert agent.interact.call_count == 3


@pytest.mark.asyncio
async def test_run_passes_tick_number(mock_agents):
    engine = SimulationEngine(mock_agents, verbose=False)
    await engine.run(ticks=2)
    anxiety = mock_agents[0]
    called_ticks = [call.args[0] for call in anxiety.maybe_post.call_args_list]
    assert called_ticks == [0, 1]


@pytest.mark.asyncio
async def test_run_zero_ticks_does_nothing(mock_agents):
    engine = SimulationEngine(mock_agents, verbose=False)
    await engine.run(ticks=0)
    for agent in mock_agents:
        agent.maybe_post.assert_not_called()
        agent.interact.assert_not_called()
