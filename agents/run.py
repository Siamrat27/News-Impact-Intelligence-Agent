"""Run one agent cycle and print the execution trace (SPEC §8 acceptance).

Usage:
    python agents/run.py                # Monitor picks a spike-flagged item
    python agents/run.py --news-id 42   # analyze a specific news item
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

load_dotenv()

from agents.graph import build_graph  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--news-id", type=int, default=None,
                        help="analyze a specific news_items.id instead of "
                             "letting the Monitor node pick one")
    args = parser.parse_args()

    graph = build_graph()
    initial = {"news_item_id": args.news_id} if args.news_id else {}

    print("=== agent trace ===")
    final_state = {}
    for step in graph.stream(initial, stream_mode="updates"):
        for node, delta in step.items():
            print(f"\n[{node}]")
            for key, value in (delta or {}).items():
                print(f"  {key} = {value}")
            final_state.update(delta or {})

    print("\n=== result ===")
    if final_state.get("decision_id"):
        print(f"agent_decisions row #{final_state['decision_id']} written.")
        print(f"Impact {final_state['impact_score']:+.2f} "
              f"@ confidence {final_state['confidence']:.2f}")
        print(f"Reasoning: {final_state['reasoning']}")
    else:
        print("No unprocessed news for any spike-flagged entity — nothing "
              "to do. (Seed data or pass --news-id.)")


if __name__ == "__main__":
    main()
