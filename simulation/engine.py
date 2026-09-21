import asyncio
from typing import List

from agents.base import AgentBase


class SimulationEngine:
    def __init__(self, agents: List[AgentBase], verbose: bool = True):
        self.agents = agents
        self.verbose = verbose

    async def run(self, ticks: int) -> None:
        for tick in range(ticks):
            if self.verbose:
                print(f"[tick {tick}]", end=" ", flush=True)
            await asyncio.gather(*[agent.maybe_post(tick) for agent in self.agents])
            await asyncio.gather(*[agent.interact(tick) for agent in self.agents])
            if self.verbose:
                print("done")
