import argparse
import asyncio
from dotenv import load_dotenv

load_dotenv()

from config import AGENTS, FOLLOWS
from db.database import Database
from agents.base import AgentBase
from simulation.engine import SimulationEngine
from simulation.feed import print_feed


def _build_agents(db: Database) -> list:
    return [
        AgentBase(
            agent_id=a["id"],
            emotion_kr=a["emotion_kr"],
            persona_prompt=a["persona_prompt"],
            aesthetic_prompt=a["aesthetic_prompt"],
            post_frequency=a["post_frequency"],
            db=db,
        )
        for a in AGENTS
    ]


def cmd_run(args: argparse.Namespace) -> None:
    db = Database()
    db.init_db()
    db.seed_agents(AGENTS)
    db.seed_follows(FOLLOWS)
    agents = _build_agents(db)
    engine = SimulationEngine(agents, verbose=True)
    asyncio.run(engine.run(ticks=args.ticks))
    print(f"\n완료: {args.ticks} ticks 시뮬레이션")


def cmd_feed(args: argparse.Namespace) -> None:
    db = Database()
    db.init_db()
    since_tick = None
    if args.ticks:
        max_tick = db.get_max_tick()
        if max_tick is not None:
            since_tick = max_tick - args.ticks + 1
    print_feed(db, agent_id=args.agent, since_tick=since_tick)


def main() -> None:
    parser = argparse.ArgumentParser(description="emotion-agents CLI")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="시뮬레이션 실행")
    run_p.add_argument("--ticks", type=int, default=24)
    run_p.set_defaults(func=cmd_run)

    feed_p = sub.add_parser("feed", help="피드 출력")
    feed_p.add_argument("--agent", type=str, default=None)
    feed_p.add_argument("--ticks", type=int, default=None)
    feed_p.set_defaults(func=cmd_feed)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
