from fastapi import APIRouter, Depends
from config import AFFINITIES
from db.database import Database
from api.deps import get_db

router = APIRouter()


@router.get("/graph")
def get_graph(db: Database = Depends(get_db)):
    stats = db.get_agent_stats()
    agents = db.conn.execute("SELECT id, emotion_kr FROM agents").fetchall()
    nodes = [
        {
            "id": r["id"],
            "emotion_kr": r["emotion_kr"],
            "post_count": stats.get(r["id"], {}).get("post_count", 0),
        }
        for r in agents
    ]
    edges = [
        {"source": src, "target": tgt, "affinity": val}
        for (src, tgt), val in AFFINITIES.items()
        if db.conn.execute("SELECT 1 FROM agents WHERE id=?", (src,)).fetchone()
        and db.conn.execute("SELECT 1 FROM agents WHERE id=?", (tgt,)).fetchone()
    ]
    return {"nodes": nodes, "edges": edges}


@router.get("/stats")
def get_stats(db: Database = Depends(get_db)):
    return db.get_agent_stats()
