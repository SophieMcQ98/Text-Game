import argparse

import Arrival
import Echoes
import Threshold
from game_engine import GameConfig, GameEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Arrival and Threshold scenes in sequence.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Use shortened Threshold timing for testing (5s wait window start).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug behaviors for scenes that support it.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    print("\n[Arrival]")
    arrival_config = GameConfig(
        player_name=Arrival.PLAYER_NAME,
        state_file=".arrival_progress.json",
    )
    arrival_engine = GameEngine(arrival_config)
    arrival_engine.run_scene(Arrival.run_scene)

    print("\n[Threshold]")
    config = GameConfig(
        player_name=Arrival.PLAYER_NAME,
        state_file=".threshold_progress.json",
        test_mode=args.test,
    )
    engine = GameEngine(config)
    engine.run_scene(Threshold.run_scene)

    print("\n[Echoes]")
    echoes_config = GameConfig(
        player_name=Arrival.PLAYER_NAME,
        state_file=".threshold_progress.json",
        test_mode=args.test,
        debug_mode=args.debug,
    )
    echoes_engine = GameEngine(echoes_config)
    echoes_engine.run_scene(Echoes.run_scene)


if __name__ == "__main__":
    main()
