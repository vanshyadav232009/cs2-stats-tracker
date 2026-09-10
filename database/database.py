import sqlite3
from pathlib import Path


class Database:
    """
    Handles the local SQLite database for CS2 match statistics.
    """

    def __init__(self, db_path="data/cs2_stats.db"):
        self.db_path = Path(db_path)

        # Create the data folder if it doesn't exist.
        self.db_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.connection = sqlite3.connect(
            self.db_path
        )

        self.create_tables()

    # ========================================================
    # DATABASE SETUP
    # ========================================================

    def create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                demo_filename TEXT NOT NULL UNIQUE,
                map_name TEXT,
                rounds INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER NOT NULL,
                player_name TEXT NOT NULL,

                kills INTEGER,
                deaths INTEGER,
                assists INTEGER,

                kd_ratio REAL,

                headshots INTEGER,
                hs_percentage REAL,

                damage REAL,
                average_damage_per_kill REAL,

                FOREIGN KEY (match_id)
                    REFERENCES matches(id),

                UNIQUE(match_id, player_name)
            )
        """)

        self.connection.commit()

    # ========================================================
    # MATCHES
    # ========================================================

    def match_exists(self, demo_filename):
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT id
            FROM matches
            WHERE demo_filename = ?
        """, (demo_filename,))

        result = cursor.fetchone()

        return result is not None

    def add_match(
        self,
        demo_filename,
        map_name,
        rounds
    ):
        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO matches (
                demo_filename,
                map_name,
                rounds
            )
            VALUES (?, ?, ?)
        """, (
            str(demo_filename),
            str(map_name),
            int(rounds)
        ))

        self.connection.commit()

        cursor.execute("""
            SELECT id
            FROM matches
            WHERE demo_filename = ?
        """, (str(demo_filename),))

        result = cursor.fetchone()

        return int(result[0])

    # ========================================================
    # PLAYER STATS
    # ========================================================

    def add_player_stats(
        self,
        match_id,
        player_name,
        stats
    ):
        cursor = self.connection.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO player_stats (
                match_id,
                player_name,
                kills,
                deaths,
                assists,
                kd_ratio,
                headshots,
                hs_percentage,
                damage,
                average_damage_per_kill
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int(match_id),
            str(player_name),
            int(stats.get("kills", 0)),
            int(stats.get("deaths", 0)),
            int(stats.get("assists", 0)),
            float(stats.get("kd_ratio", 0)),
            int(stats.get("headshots", 0)),
            float(stats.get("hs_percentage", 0)),
            float(stats.get("damage", 0)),
            float(stats.get("average_damage_per_kill", 0))
        ))

        self.connection.commit()

    # ========================================================
    # GET ALL MATCHES
    # ========================================================

    def get_matches(self):
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                id,
                demo_filename,
                map_name,
                rounds,
                created_at
            FROM matches
            ORDER BY id DESC
        """)

        return cursor.fetchall()

    # ========================================================
    # GET PLAYER MATCH HISTORY
    # ========================================================

    def get_player_matches(self, player_name):
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                matches.id,
                matches.demo_filename,
                matches.map_name,
                matches.rounds,
                player_stats.kills,
                player_stats.deaths,
                player_stats.assists,
                player_stats.kd_ratio,
                player_stats.headshots,
                player_stats.hs_percentage,
                player_stats.damage,
                player_stats.average_damage_per_kill,
                matches.created_at
            FROM player_stats

            JOIN matches
                ON player_stats.match_id = matches.id

            WHERE player_stats.player_name = ?

            ORDER BY matches.id DESC
        """, (str(player_name),))

        return cursor.fetchall()

    # ========================================================
    # OVERALL STATS
    # ========================================================

    def get_overall_stats(self, player_name):
        cursor = self.connection.cursor()

        cursor.execute("""
            SELECT
                COUNT(*),
                SUM(kills),
                SUM(deaths),
                SUM(assists),
                SUM(headshots),
                SUM(damage),
                AVG(hs_percentage),
                AVG(kd_ratio)
            FROM player_stats

            WHERE player_name = ?
        """, (str(player_name),))

        result = cursor.fetchone()

        if not result or result[0] == 0:
            return None

        return {
            "matches": int(result[0]),
            "kills": int(result[1] or 0),
            "deaths": int(result[2] or 0),
            "assists": int(result[3] or 0),
            "headshots": int(result[4] or 0),
            "damage": float(result[5] or 0),
            "average_hs_percentage": float(result[6] or 0),
            "average_kd": float(result[7] or 0)
        }

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):
        self.connection.close()