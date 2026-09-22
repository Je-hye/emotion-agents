from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from db.database import Database
from api.deps import get_db

router = APIRouter()


class ScoreUpdate(BaseModel):
    score: float


def _post_to_dict(post, interactions):
    return {
        "id": post.id,
        "agent_id": post.agent_id,
        "caption": post.caption,
        "image_url": f"/data/images/{post.agent_id}_{post.tick}.png" if post.image_path else None,
        "tick": post.tick,
        "quality_score": post.quality_score,
        "interactions": interactions,
    }


@router.get("/posts")
def get_posts(
    agent_id: Optional[str] = None,
    since_tick: Optional[int] = None,
    min_score: Optional[float] = None,
    db: Database = Depends(get_db),
):
    posts = db.get_all_posts(agent_id=agent_id, since_tick=since_tick)
    result = []
    for post in posts:
        if min_score is not None and (post.quality_score is None or post.quality_score < min_score):
            continue
        interactions = db.get_interactions_for_post(post.id)
        result.append(_post_to_dict(post, interactions))
    return sorted(result, key=lambda x: (x["tick"], x["id"]), reverse=True)


@router.get("/posts/{post_id}")
def get_post(post_id: int, db: Database = Depends(get_db)):
    posts = db.get_all_posts()
    post = next((p for p in posts if p.id == post_id), None)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    interactions = db.get_interactions_for_post(post.id)
    return _post_to_dict(post, interactions)


@router.patch("/posts/{post_id}/score")
def update_score(post_id: int, body: ScoreUpdate, db: Database = Depends(get_db)):
    db.update_quality_score(post_id, body.score)
    return {"post_id": post_id, "score": body.score}
