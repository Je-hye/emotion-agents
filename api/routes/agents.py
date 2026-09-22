from fastapi import APIRouter, Depends
from db.database import Database
from api.deps import get_db

router = APIRouter()


@router.get("/agents")
def get_agents(db: Database = Depends(get_db)):
    rows = db.conn.execute(
        "SELECT id, emotion_kr, post_frequency FROM agents ORDER BY id"
    ).fetchall()
    return [{"id": r["id"], "emotion_kr": r["emotion_kr"], "post_frequency": r["post_frequency"]} for r in rows]
