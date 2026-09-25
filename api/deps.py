import os
from db.database import Database

_db: Database | None = None


def get_db() -> Database:
    global _db
    if _db is None:
        db_path = os.environ.get("DB_PATH", "emotion_agents.db")
        _db = Database(db_path)
        _db.init_db()
    return _db
