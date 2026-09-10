from pathlib import Path
from demoparser2 import DemoParser
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

DEMO_FOLDER = Path("demos")


# ============================================================
# FIND DEMO
# ============================================================

demo_files = list(DEMO_FOLDER.glob("*.dem"))

if not demo_files:
    print("ERROR: No .dem file found in the demos folder.")
    raise SystemExit

if len(demo_files) > 1:
    print("Multiple demos found. Using the first one:")
    for demo in demo_files:
        print(f"  - {demo.name}")

demo_path = demo_files[0]


# ============================================================
# LOAD DEMO
# ============================================================

print("=" * 60)
print("              CS2 STATS TRACKER")
print("=" * 60)

print()
print(f"Loading demo: {demo_path.name}")

parser = DemoParser(str(demo_path))


# ============================================================
# HEADER
# ============================================================

header = parser.parse_header()

map_name = header.get("map_name", "Unknown")

print()
print("Demo loaded successfully!")
print(f"Map: {map_name}")


# ============================================================
# PLAYER INFORMATION
# ============================================================

player_info = parser.parse_player_info()

# We identify the player from the demo events instead of relying
# on parse_player_info(), because some demos may not populate it.

deaths = parser.parse_event("player_death")

if deaths.empty:
    print()
    print("ERROR: No player_death events found.")
    raise SystemExit


# Find player names appearing as attackers/victims.
possible_players = set()

if "attacker_name" in deaths.columns:
    possible_players.update(
        deaths["attacker_name"]
        .dropna()
        .astype(str)
        .tolist()
    )

if "user_name" in deaths.columns:
    possible_players.update(
        deaths["user_name"]
        .dropna()
        .astype(str)
        .tolist()
    )

# Remove generic/world events.
possible_players.discard("world")
possible_players.discard("")

if not possible_players:
    print()
    print("ERROR: Could not identify players in the demo.")
    raise SystemExit


# ============================================================
# SELECT PLAYER
# ============================================================

# If your name is known, put it here.
# Leave as None to automatically use the first player found.

PLAYER_NAME = "Ｓ Ａ Ｎ Ｅ Ｍ Ｉ"

if PLAYER_NAME is None:
    player_name = sorted(possible_players)[0]
else:
    player_name = PLAYER_NAME

print(f"Player: {player_name}")


# ============================================================
# CLEAN DEATH EVENTS
# ============================================================

# Remove world/self events.
real_deaths = deaths[
    deaths["attacker_name"].notna()
    & deaths["user_name"].notna()
    & (deaths["attacker_name"] != deaths["user_name"])
].copy()


# ============================================================
# KILLS
# ============================================================

kills = real_deaths[
    real_deaths["attacker_name"] == player_name
].copy()


# ============================================================
# DEATHS
# ============================================================

deaths_taken = real_deaths[
    real_deaths["user_name"] == player_name
].copy()


# ============================================================
# ASSISTS
# ============================================================

if "assister_name" in real_deaths.columns:
    assists = real_deaths[
        real_deaths["assister_name"] == player_name
    ].copy()
else:
    assists = pd.DataFrame()


# ============================================================
# HEADSHOTS
# ============================================================

if "headshot" in kills.columns:
    headshots = int(kills["headshot"].fillna(False).astype(bool).sum())
else:
    headshots = 0


# ============================================================
# BASIC STATS
# ============================================================

kill_count = len(kills)
death_count = len(deaths_taken)
assist_count = len(assists)

if death_count > 0:
    kd_ratio = kill_count / death_count
else:
    kd_ratio = float("inf")

if kill_count > 0:
    hs_percentage = (headshots / kill_count) * 100
else:
    hs_percentage = 0.0


# ============================================================
# DAMAGE
# ============================================================

print()
print("Reading damage events...")

try:
    damage_events = parser.parse_event("player_hurt")

    if not damage_events.empty and "attacker_name" in damage_events.columns:
        player_damage = damage_events[
            damage_events["attacker_name"] == player_name
        ].copy()

        if "dmg_health" in player_damage.columns:
            total_damage = (
                pd.to_numeric(
                    player_damage["dmg_health"],
                    errors="coerce"
                )
                .fillna(0)
                .sum()
            )
        else:
            total_damage = 0

    else:
        player_damage = pd.DataFrame()
        total_damage = 0

except Exception as error:
    print(f"Damage events unavailable: {error}")
    player_damage = pd.DataFrame()
    total_damage = 0


if kill_count > 0:
    average_damage_per_kill = total_damage / kill_count
else:
    average_damage_per_kill = 0


# ============================================================
# ROUND INFORMATION
# ============================================================

print("Reading round information...")

try:
    round_events = parser.parse_event(
        "round_end",
        other=[
            "total_rounds_played",
            "is_warmup_period"
        ]
    )

    if not round_events.empty:
        if "is_warmup_period" in round_events.columns:
            real_rounds = round_events[
                round_events["is_warmup_period"] != True
            ].copy()
        else:
            real_rounds = round_events.copy()

        if "total_rounds_played" in real_rounds.columns:
            round_numbers = pd.to_numeric(
                real_rounds["total_rounds_played"],
                errors="coerce"
            ).dropna()

            if not round_numbers.empty:
                total_rounds = int(round_numbers.max())
            else:
                total_rounds = len(real_rounds)
        else:
            total_rounds = len(real_rounds)

    else:
        total_rounds = 0

except Exception as error:
    print(f"Round information unavailable: {error}")
    total_rounds = 0


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 60)
print("                    MATCH STATS")
print("=" * 60)

print(f"Player:                 {player_name}")
print(f"Map:                    {map_name}")
print()
print(f"Kills:                  {kill_count}")
print(f"Deaths:                 {death_count}")
print(f"Assists:                {assist_count}")
print(f"K/D Ratio:              {kd_ratio:.2f}")
print()
print(f"Headshots:              {headshots}")
print(f"Headshot %:             {hs_percentage:.1f}%")
print()
print(f"Damage dealt:           {total_damage:.0f}")
print(f"Average damage / kill:  {average_damage_per_kill:.1f}")
print()
print(f"Rounds played:          {total_rounds}")

print("=" * 60)


# ============================================================
# YOUR KILL EVENTS
# ============================================================

print()
print("=" * 60)
print("                  YOUR KILL EVENTS")
print("=" * 60)

if kills.empty:
    print("No kills found.")
else:

    columns_to_show = [
        column
        for column in [
            "tick",
            "user_name",
            "headshot",
            "distance"
        ]
        if column in kills.columns
    ]

    print(
        kills[columns_to_show].to_string(index=False)
    )


# ============================================================
# YOUR DEATH EVENTS
# ============================================================

print()
print("=" * 60)
print("                 YOUR DEATH EVENTS")
print("=" * 60)

if deaths_taken.empty:
    print("No deaths found.")
else:

    columns_to_show = [
        column
        for column in [
            "tick",
            "attacker_name",
            "headshot",
            "distance"
        ]
        if column in deaths_taken.columns
    ]

    print(
        deaths_taken[columns_to_show].to_string(index=False)
    )


# ============================================================
# DAMAGE SUMMARY
# ============================================================

print()
print("=" * 60)
print("                    DAMAGE")
print("=" * 60)

if player_damage.empty:
    print("No damage events found.")
else:
    print(f"Damage events:          {len(player_damage)}")
    print(f"Total damage:           {total_damage:.0f}")
    print(f"Average damage / kill:  {average_damage_per_kill:.1f}")


print()
print("Analysis complete.")