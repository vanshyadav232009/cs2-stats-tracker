from pathlib import Path

from demoparser2 import DemoParser


class CS2DemoParser:
    """
    Handles loading a CS2 demo and extracting raw demo data.

    This class does NOT calculate statistics.
    It only talks to demoparser2 and returns the raw data.
    """

    def __init__(self, demo_path):
        self.demo_path = Path(demo_path)

        if not self.demo_path.exists():
            raise FileNotFoundError(
                f"Demo file not found: {self.demo_path}"
            )

        if self.demo_path.suffix.lower() != ".dem":
            raise ValueError(
                "The selected file is not a CS2 .dem file."
            )

        self.parser = DemoParser(str(self.demo_path))

    # ========================================================
    # DEMO INFORMATION
    # ========================================================

    def get_header(self):
        """Return the demo header information."""
        return self.parser.parse_header()

    def get_map_name(self):
        """Return the map name."""
        header = self.get_header()
        return header.get("map_name", "Unknown")

    # ========================================================
    # PLAYER INFORMATION
    # ========================================================

    def get_player_info(self):
        """Return player information from the demo."""
        return self.parser.parse_player_info()

    # ========================================================
    # GAME EVENTS
    # ========================================================

    def get_death_events(self):
        """Return all player_death events."""
        return self.parser.parse_event("player_death")

    def get_damage_events(self):
        """Return all player_hurt events."""
        return self.parser.parse_event("player_hurt")

    def get_round_events(self):
        """Return all round_end events."""
        return self.parser.parse_event(
            "round_end",
            other=[
                "total_rounds_played",
                "is_warmup_period"
            ]
        )

    # ========================================================
    # PLAYER NAMES
    # ========================================================

    def get_player_names(self):
        """
        Get player names from death events.

        Some demos may return an empty result from
        parse_player_info(), so we use actual game events
        as a reliable fallback.
        """

        deaths = self.get_death_events()

        if deaths.empty:
            return []

        players = set()

        if "attacker_name" in deaths.columns:
            players.update(
                deaths["attacker_name"]
                .dropna()
                .astype(str)
                .tolist()
            )

        if "user_name" in deaths.columns:
            players.update(
                deaths["user_name"]
                .dropna()
                .astype(str)
                .tolist()
            )

        # Remove non-player events
        players.discard("")
        players.discard("world")

        return sorted(players)

    # ========================================================
    # BASIC DEMO SUMMARY
    # ========================================================

    def get_summary(self):
        """
        Return basic information about the demo.
        """

        return {
            "file_name": self.demo_path.name,
            "file_path": str(self.demo_path),
            "map": self.get_map_name(),
            "players": self.get_player_names(),
        }