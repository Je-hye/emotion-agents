import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class Post:
    id: int
    agent_id: str
    caption: str
    image_path: Optional[str]
    tick: int
    quality_score: Optional[float] = None


class Database:
    def __init__(self, db_path: str = "emotion_agents.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def init_db(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"
        self.conn.executescript(schema_path.read_text())
        self.conn.commit()

    def seed_agents(self, agents_data: List[dict]) -> None:
        for a in agents_data:
            self.conn.execute(
                "INSERT OR IGNORE INTO agents VALUES (?, ?, ?, ?, ?)",
                (a["id"], a["emotion_kr"], a["persona_prompt"],
                 a["aesthetic_prompt"], a["post_frequency"]),
            )
        self.conn.commit()

    def seed_follows(self, follows: List[tuple]) -> None:
        for follower, following in follows:
            self.conn.execute(
                "INSERT OR IGNORE INTO follows VALUES (?, ?)",
                (follower, following),
            )
        self.conn.commit()

    def save_post(
        self,
        agent_id: str,
        caption: str,
        image_path: Optional[str],
        tick: int,
    ) -> int:
        cur = self.conn.execute(
            "INSERT INTO posts (agent_id, caption, image_path, tick) VALUES (?, ?, ?, ?)",
            (agent_id, caption, image_path, tick),
        )
        self.conn.commit()
        return cur.lastrowid

    def save_interaction(
        self,
        from_agent: str,
        to_post: int,
        type: str,
        content: Optional[str],
        tick: int,
    ) -> None:
        self.conn.execute(
            "INSERT INTO interactions (from_agent, to_post, type, content, tick) VALUES (?, ?, ?, ?, ?)",
            (from_agent, to_post, type, content, tick),
        )
        self.conn.commit()

    def get_recent_posts(
        self,
        exclude_agent_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[Post]:
        if exclude_agent_id:
            rows = self.conn.execute(
                "SELECT id, agent_id, caption, image_path, tick, quality_score FROM posts "
                "WHERE agent_id != ? ORDER BY tick DESC, id DESC LIMIT ?",
                (exclude_agent_id, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT id, agent_id, caption, image_path, tick, quality_score FROM posts "
                "ORDER BY tick DESC, id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [Post(r["id"], r["agent_id"], r["caption"], r["image_path"], r["tick"], r["quality_score"]) for r in rows]

    def get_recent_stimuli(self, agent_id: str, since_tick: int) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM interactions i "
            "JOIN posts p ON i.to_post = p.id "
            "WHERE p.agent_id = ? AND i.tick >= ?",
            (agent_id, since_tick),
        ).fetchone()
        return row[0]

    def get_all_posts(
        self,
        agent_id: Optional[str] = None,
        since_tick: Optional[int] = None,
    ) -> List[Post]:
        query = "SELECT id, agent_id, caption, image_path, tick, quality_score FROM posts"
        params: list = []
        conditions = []
        if agent_id:
            conditions.append("agent_id = ?")
            params.append(agent_id)
        if since_tick is not None:
            conditions.append("tick >= ?")
            params.append(since_tick)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY tick ASC, id ASC"
        rows = self.conn.execute(query, params).fetchall()
        return [Post(r["id"], r["agent_id"], r["caption"], r["image_path"], r["tick"], r["quality_score"]) for r in rows]

    def get_interactions_for_post(self, post_id: int) -> List[dict]:
        rows = self.conn.execute(
            "SELECT from_agent, type, content FROM interactions "
            "WHERE to_post = ? ORDER BY id ASC",
            (post_id,),
        ).fetchall()
        return [{"from_agent": r["from_agent"], "type": r["type"], "content": r["content"]} for r in rows]

    def get_max_tick(self) -> Optional[int]:
        row = self.conn.execute("SELECT MAX(tick) FROM posts").fetchone()
        return row[0]

    def update_quality_score(self, post_id: int, score: float) -> None:
        self.conn.execute(
            "UPDATE posts SET quality_score = ? WHERE id = ?",
            (score, post_id),
        )
        self.conn.commit()

    def get_agent_stats(self) -> dict:
        agents = self.conn.execute("SELECT id FROM agents").fetchall()
        stats = {}
        for row in agents:
            agent_id = row["id"]
            post_count = self.conn.execute(
                "SELECT COUNT(*) FROM posts WHERE agent_id = ?", (agent_id,)
            ).fetchone()[0]
            likes = self.conn.execute(
                "SELECT COUNT(*) FROM interactions i JOIN posts p ON i.to_post = p.id "
                "WHERE p.agent_id = ? AND i.type = 'like'", (agent_id,)
            ).fetchone()[0]
            comments = self.conn.execute(
                "SELECT COUNT(*) FROM interactions i JOIN posts p ON i.to_post = p.id "
                "WHERE p.agent_id = ? AND i.type = 'comment'", (agent_id,)
            ).fetchone()[0]
            stats[agent_id] = {
                "post_count": post_count,
                "received_likes": likes,
                "received_comments": comments,
            }
        return stats
