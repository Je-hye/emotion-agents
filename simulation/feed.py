from typing import List, Optional

from db.database import Database, Post


def format_post(post: Post, interactions: List[dict]) -> str:
    lines = [f"[tick {post.tick}] @{post.agent_id}"]
    lines.append(f'  "{post.caption}"')
    if post.image_path:
        lines.append(f"  🖼  {post.image_path}")
    for i in interactions:
        if i["type"] == "like":
            lines.append(f"  ❤  @{i['from_agent']}")
        else:
            lines.append(f"  💬 @{i['from_agent']}: \"{i['content']}\"")
    return "\n".join(lines)


def print_feed(
    db: Database,
    agent_id: Optional[str] = None,
    since_tick: Optional[int] = None,
) -> None:
    posts = db.get_all_posts(agent_id=agent_id, since_tick=since_tick)
    for post in posts:
        interactions = db.get_interactions_for_post(post.id)
        print(format_post(post, interactions))
        print()
