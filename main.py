from pathlib import Path

from parser.demo_parser import CS2DemoParser
from analysis.stats import CS2Stats
from database.database import Database


DEMO_FOLDER = Path("demos")


def main():
    demo_files = list(DEMO_FOLDER.glob("*.dem"))

    if not demo_files:
        print("No demos found.")
        return

    database = Database()

    for demo_path in demo_files:
        print(f"\nProcessing: {demo_path.name}")

        # --------------------------------------------
        # Parse demo
        # --------------------------------------------

        demo = CS2DemoParser(demo_path)

        map_name = demo.get_map_name()
        death_events = demo.get_death_events()
        damage_events = demo.get_damage_events()
        round_events = demo.get_round_events()

        # --------------------------------------------
        # Calculate rounds
        # --------------------------------------------

        stats_engine = CS2Stats(
            death_events,
            damage_events,
            round_events
        )

        rounds = stats_engine.calculate_rounds()

        # --------------------------------------------
        # Skip already imported demos
        # --------------------------------------------

        if database.match_exists(
            demo_path.name
        ):
            print("Already imported. Skipping.")
            continue

        # --------------------------------------------
        # Add match
        # --------------------------------------------

        match_id = database.add_match(
            demo_filename=demo_path.name,
            map_name=map_name,
            rounds=rounds
        )

        # --------------------------------------------
        # Find players
        # --------------------------------------------

        players = demo.get_player_names()

        # --------------------------------------------
        # Calculate and save every player's stats
        # --------------------------------------------

        for player_name in players:

            player_stats = stats_engine.calculate_all(
                player_name
            )

            database.add_player_stats(
                match_id,
                player_name,
                player_stats
            )

            print(
                f"  {player_name}: "
                f"{player_stats['kills']} / "
                f"{player_stats['deaths']} / "
                f"{player_stats['assists']}"
            )

    database.close()

    print("\nAll demos processed.")


if __name__ == "__main__":
    main()