import pandas as pd


class CS2Stats:
    """
    Calculates player statistics from raw CS2 demo events.
    """

    def __init__(self, death_events, damage_events=None, round_events=None):
        self.deaths = death_events.copy()
        self.damage_events = (
            damage_events.copy()
            if damage_events is not None
            else pd.DataFrame()
        )
        self.round_events = (
            round_events.copy()
            if round_events is not None
            else pd.DataFrame()
        )

    # ========================================================
    # CLEAN EVENTS
    # ========================================================

    def get_real_deaths(self):
        """
        Remove world/self events that aren't normal kills.
        """

        if self.deaths.empty:
            return self.deaths

        return self.deaths[
            self.deaths["attacker_name"].notna()
            & self.deaths["user_name"].notna()
            & (
                self.deaths["attacker_name"]
                != self.deaths["user_name"]
            )
        ].copy()

    # ========================================================
    # PLAYER EVENTS
    # ========================================================

    def get_kills(self, player_name):
        deaths = self.get_real_deaths()

        return deaths[
            deaths["attacker_name"] == player_name
        ].copy()

    def get_deaths(self, player_name):
        deaths = self.get_real_deaths()

        return deaths[
            deaths["user_name"] == player_name
        ].copy()

    def get_assists(self, player_name):
        deaths = self.get_real_deaths()

        if "assister_name" not in deaths.columns:
            return pd.DataFrame()

        return deaths[
            deaths["assister_name"] == player_name
        ].copy()

    # ========================================================
    # K/D/A
    # ========================================================

    def calculate_kda(self, player_name):
        kills = self.get_kills(player_name)
        deaths = self.get_deaths(player_name)
        assists = self.get_assists(player_name)

        kill_count = len(kills)
        death_count = len(deaths)
        assist_count = len(assists)

        if death_count > 0:
            kd_ratio = kill_count / death_count
        else:
            kd_ratio = 0

        return {
            "kills": kill_count,
            "deaths": death_count,
            "assists": assist_count,
            "kd_ratio": kd_ratio,
        }

    # ========================================================
    # HEADSHOTS
    # ========================================================

    def calculate_headshots(self, player_name):
        kills = self.get_kills(player_name)

        if kills.empty or "headshot" not in kills.columns:
            return {
                "headshots": 0,
                "hs_percentage": 0.0,
            }

        headshots = int(
            kills["headshot"]
            .fillna(False)
            .astype(bool)
            .sum()
        )

        kill_count = len(kills)

        if kill_count > 0:
            hs_percentage = (
                headshots / kill_count
            ) * 100
        else:
            hs_percentage = 0.0

        return {
            "headshots": headshots,
            "hs_percentage": hs_percentage,
        }

    # ========================================================
    # DAMAGE
    # ========================================================

    def calculate_damage(self, player_name):
        if self.damage_events.empty:
            return {
                "damage": 0,
                "damage_events": 0,
                "average_damage_per_kill": 0.0,
            }

        if "attacker_name" not in self.damage_events.columns:
            return {
                "damage": 0,
                "damage_events": 0,
                "average_damage_per_kill": 0.0,
            }

        player_damage = self.damage_events[
            self.damage_events["attacker_name"]
            == player_name
        ].copy()

        if "dmg_health" not in player_damage.columns:
            total_damage = 0
        else:
            total_damage = (
                pd.to_numeric(
                    player_damage["dmg_health"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )

        kills = self.get_kills(player_name)
        kill_count = len(kills)

        if kill_count > 0:
            average_damage = (
                total_damage / kill_count
            )
        else:
            average_damage = 0.0

        return {
            "damage": total_damage,
            "damage_events": len(player_damage),
            "average_damage_per_kill": average_damage,
        }

    # ========================================================
    # ROUNDS
    # ========================================================

    def calculate_rounds(self):
        if self.round_events.empty:
            return 0

        rounds = self.round_events.copy()

        if "is_warmup_period" in rounds.columns:
            rounds = rounds[
                rounds["is_warmup_period"] != True
            ]

        if "total_rounds_played" in rounds.columns:
            round_numbers = pd.to_numeric(
                rounds["total_rounds_played"],
                errors="coerce"
            ).dropna()

            if not round_numbers.empty:
                return int(round_numbers.max())

        return len(rounds)

    # ========================================================
    # COMPLETE PLAYER STATS
    # ========================================================

    def calculate_all(self, player_name):
        kda = self.calculate_kda(player_name)
        headshots = self.calculate_headshots(player_name)
        damage = self.calculate_damage(player_name)
        rounds = self.calculate_rounds()

        return {
            **kda,
            **headshots,
            **damage,
            "rounds": rounds,
        }