import asyncio
import logging
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field

from api.deps import get_db
from config import AGENTS, FOLLOWS
from agents.base import AgentBase

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active: List[WebSocket] = []
        self._running = False
        self._task: asyncio.Task | None = None

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active = [c for c in self.active if c is not ws]

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def cancel(self):
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._running = False
        self._task = None


manager = ConnectionManager()


@router.websocket("/ws/ticks")
async def ws_ticks(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


class SimulateRequest(BaseModel):
    ticks: int = Field(ge=1, le=100)


@router.post("/api/simulate")
async def run_simulate(body: SimulateRequest):
    if manager._running:
        raise HTTPException(status_code=409, detail="Simulation already running")
    manager._running = True

    db = get_db()
    agents = [
        AgentBase(
            agent_id=cfg["id"],
            emotion_kr=cfg["emotion_kr"],
            persona_prompt=cfg["persona_prompt"],
            aesthetic_prompt=cfg["aesthetic_prompt"],
            post_frequency=cfg["post_frequency"],
            db=db,
        )
        for cfg in AGENTS
    ]
    db.seed_follows(FOLLOWS)

    async def run():
        try:
            for tick in range(body.ticks):
                await asyncio.gather(*[a.maybe_post(tick) for a in agents])
                await asyncio.gather(*[a.interact(tick) for a in agents])
                await manager.broadcast({"type": "tick", "tick": tick})
            await manager.broadcast({"type": "done", "ticks": body.ticks})
        except asyncio.CancelledError:
            await manager.broadcast({"type": "cancelled"})
            raise
        except Exception as exc:
            logging.error("Simulation error: %s", exc)
            await manager.broadcast({"type": "error", "detail": str(exc)})
        finally:
            manager._running = False
            manager._task = None

    manager._task = asyncio.create_task(run())
    return {"status": "started", "ticks": body.ticks}


@router.delete("/api/simulate")
async def cancel_simulate():
    if not manager._running:
        raise HTTPException(status_code=404, detail="No simulation running")
    await manager.cancel()
    return {"status": "cancelled"}
