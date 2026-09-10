import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading

import pandas as pd
from demoparser2 import DemoParser


class CS2StatsTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("CS2 Stats Tracker")
        self.root.geometry("1100x750")
        self.root.minsize(900, 650)

        self.parser = None
        self.deaths = None
        self.demo_path = None
        self.player_names = []

        self.setup_style()
        self.create_ui()

    # ========================================================
    # STYLE
    # ========================================================

    def setup_style(self):
        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TFrame",
            background="#111318"
        )

        style.configure(
            "TLabel",
            background="#111318",
            foreground="#E8E8E8",
            font=("Segoe UI", 10)
        )

        style.configure(
            "Title.TLabel",
            background="#111318",
            foreground="#FFFFFF",
            font=("Segoe UI", 24, "bold")
        )

        style.configure(
            "Subtitle.TLabel",
            background="#111318",
            foreground="#8F96A3",
            font=("Segoe UI", 10)
        )

        style.configure(
            "Card.TFrame",
            background="#1A1D23"
        )

        style.configure(
            "CardTitle.TLabel",
            background="#1A1D23",
            foreground="#8F96A3",
            font=("Segoe UI", 9)
        )

        style.configure(
            "CardValue.TLabel",
            background="#1A1D23",
            foreground="#FFFFFF",
            font=("Segoe UI", 20, "bold")
        )

        style.configure(
            "Accent.TButton",
            font=("Segoe UI", 10, "bold"),
            padding=(15, 8)
        )

        style.configure(
            "TCombobox",
            padding=6
        )

        style.configure(
            "Treeview",
            background="#181B20",
            foreground="#E8E8E8",
            fieldbackground="#181B20",
            rowheight=28,
            font=("Segoe UI", 9)
        )

        style.configure(
            "Treeview.Heading",
            background="#252932",
            foreground="#FFFFFF",
            font=("Segoe UI", 9, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", "#34495E")],
            foreground=[("selected", "#FFFFFF")]
        )

    # ========================================================
    # UI
    # ========================================================

    def create_ui(self):
        self.root.configure(bg="#111318")

        main = ttk.Frame(self.root, padding=25)
        main.pack(fill="both", expand=True)

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        ttk.Label(
            main,
            text="CS2 STATS TRACKER",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            main,
            text="Automatic Counter-Strike 2 demo analysis",
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(0, 20))

        # ----------------------------------------------------
        # DEMO CONTROLS
        # ----------------------------------------------------

        controls = ttk.Frame(main, style="Card.TFrame", padding=15)
        controls.pack(fill="x", pady=(0, 15))

        ttk.Label(
            controls,
            text="DEMO FILE"
        ).pack(side="left")

        self.demo_label = ttk.Label(
            controls,
            text="No demo selected",
            style="Subtitle.TLabel"
        )
        self.demo_label.pack(side="left", padx=15)

        self.load_button = ttk.Button(
            controls,
            text="Load Demo",
            style="Accent.TButton",
            command=self.select_demo
        )
        self.load_button.pack(side="right")

        # ----------------------------------------------------
        # PLAYER SELECTOR
        # ----------------------------------------------------

        player_frame = ttk.Frame(main)
        player_frame.pack(fill="x", pady=(0, 15))

        ttk.Label(
            player_frame,
            text="Player:"
        ).pack(side="left")

        self.player_var = tk.StringVar()

        self.player_combo = ttk.Combobox(
            player_frame,
            textvariable=self.player_var,
            state="readonly",
            width=35
        )

        self.player_combo.pack(side="left", padx=10)

        self.player_combo.bind(
            "<<ComboboxSelected>>",
            self.player_changed
        )

        self.status_var = tk.StringVar(
            value="Load a CS2 demo to begin."
        )

        ttk.Label(
            player_frame,
            textvariable=self.status_var,
            style="Subtitle.TLabel"
        ).pack(side="left", padx=15)

        # ----------------------------------------------------
        # MATCH INFO
        # ----------------------------------------------------

        info_frame = ttk.Frame(main)
        info_frame.pack(fill="x", pady=(0, 15))

        self.map_label = ttk.Label(
            info_frame,
            text="Map: -"
        )
        self.map_label.pack(side="left")

        self.round_label = ttk.Label(
            info_frame,
            text="Rounds: -"
        )
        self.round_label.pack(side="left", padx=30)

        # ----------------------------------------------------
        # STAT CARDS
        # ----------------------------------------------------

        stats_frame = ttk.Frame(main)
        stats_frame.pack(fill="x", pady=(0, 20))

        self.stat_cards = {}

        stats = [
            ("Kills", "kills"),
            ("Deaths", "deaths"),
            ("Assists", "assists"),
            ("K/D", "kd"),
            ("Headshots", "headshots"),
            ("HS %", "hs_percent"),
            ("Damage", "damage"),
            ("ADR / Kill", "avg_damage")
        ]

        for title, key in stats:
            card = ttk.Frame(
                stats_frame,
                style="Card.TFrame",
                padding=12
            )

            card.pack(
                side="left",
                fill="both",
                expand=True,
                padx=4
            )

            ttk.Label(
                card,
                text=title,
                style="CardTitle.TLabel"
            ).pack()

            value = ttk.Label(
                card,
                text="-",
                style="CardValue.TLabel"
            )

            value.pack(pady=(5, 0))

            self.stat_cards[key] = value

        # ----------------------------------------------------
        # EVENT TABLES
        # ----------------------------------------------------

        notebook = ttk.Notebook(main)
        notebook.pack(fill="both", expand=True)

        # KILLS TAB
        kills_tab = ttk.Frame(notebook)
        notebook.add(kills_tab, text="  Your Kills  ")

        self.kills_tree = self.create_tree(
            kills_tab,
            [
                ("tick", "Tick", 100),
                ("victim", "Victim", 250),
                ("weapon", "Weapon", 160),
                ("headshot", "Headshot", 100),
                ("distance", "Distance", 120)
            ]
        )

        # DEATHS TAB
        deaths_tab = ttk.Frame(notebook)
        notebook.add(deaths_tab, text="  Your Deaths  ")

        self.deaths_tree = self.create_tree(
            deaths_tab,
            [
                ("tick", "Tick", 100),
                ("killer", "Killer", 250),
                ("weapon", "Weapon", 160),
                ("headshot", "Headshot", 100),
                ("distance", "Distance", 120)
            ]
        )

        # ----------------------------------------------------
        # STATUS BAR
        # ----------------------------------------------------

        ttk.Label(
            main,
            textvariable=self.status_var,
            style="Subtitle.TLabel"
        ).pack(anchor="w", pady=(10, 0))

    # ========================================================
    # TREEVIEW CREATOR
    # ========================================================

    def create_tree(self, parent, columns):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)

        column_ids = [column[0] for column in columns]

        tree = ttk.Treeview(
            frame,
            columns=column_ids,
            show="headings"
        )

        for key, heading, width in columns:
            tree.heading(key, text=heading)
            tree.column(
                key,
                width=width,
                anchor="center"
            )

        scrollbar = ttk.Scrollbar(
            frame,
            orient="vertical",
            command=tree.yview
        )

        tree.configure(
            yscrollcommand=scrollbar.set
        )

        tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        return tree

    # ========================================================
    # SELECT DEMO
    # ========================================================

    def select_demo(self):
        file_path = filedialog.askopenfilename(
            title="Select CS2 Demo",
            filetypes=[
                ("CS2 Demo", "*.dem"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        self.demo_path = Path(file_path)

        self.demo_label.config(
            text=self.demo_path.name
        )

        self.status_var.set(
            "Loading demo..."
        )

        self.load_button.config(
            state="disabled"
        )

        threading.Thread(
            target=self.load_demo,
            daemon=True
        ).start()

    # ========================================================
    # LOAD DEMO
    # ========================================================

    def load_demo(self):
        try:
            parser = DemoParser(
                str(self.demo_path)
            )

            header = parser.parse_header()

            deaths = parser.parse_event(
                "player_death"
            )

            if deaths.empty:
                raise ValueError(
                    "No player death events were found."
                )

            # Find all players from events
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

            players.discard("")
            players.discard("world")

            self.parser = parser
            self.deaths = deaths
            self.player_names = sorted(players)

            map_name = header.get(
                "map_name",
                "Unknown"
            )

            self.root.after(
                0,
                lambda: self.demo_loaded(
                    map_name
                )
            )

        except Exception as error:
            self.root.after(
                0,
                lambda: self.load_failed(
                    str(error)
                )
            )

    # ========================================================
    # DEMO LOADED
    # ========================================================

    def demo_loaded(self, map_name):
        self.load_button.config(
            state="normal"
        )

        self.player_combo["values"] = (
            self.player_names
        )

        if self.player_names:
            # Automatically select SANEMI if present
            sanemi = next(
                (
                    name
                    for name in self.player_names
                    if "Ｓ Ａ Ｎ Ｅ Ｍ Ｉ" in name
                ),
                None
            )

            if sanemi:
                self.player_var.set(sanemi)
            else:
                self.player_var.set(
                    self.player_names[0]
                )

            self.player_combo.current(
                self.player_names.index(
                    self.player_var.get()
                )
            )

        self.map_label.config(
            text=f"Map: {map_name}"
        )

        self.status_var.set(
            "Demo loaded successfully."
        )

        self.update_stats()

    # ========================================================
    # LOAD FAILED
    # ========================================================

    def load_failed(self, error):
        self.load_button.config(
            state="normal"
        )

        self.status_var.set(
            "Failed to load demo."
        )

        messagebox.showerror(
            "Demo Loading Error",
            f"Could not load the demo:\n\n{error}"
        )

    # ========================================================
    # PLAYER CHANGED
    # ========================================================

    def player_changed(self, event=None):
        self.update_stats()

    # ========================================================
    # UPDATE STATS
    # ========================================================

    def update_stats(self):
        if self.deaths is None:
            return

        player_name = self.player_var.get()

        if not player_name:
            return

        deaths = self.deaths

        # Remove invalid world/self events
        real_deaths = deaths[
            deaths["attacker_name"].notna()
            & deaths["user_name"].notna()
            & (
                deaths["attacker_name"]
                != deaths["user_name"]
            )
        ].copy()

        # ----------------------------------------------------
        # KILLS
        # ----------------------------------------------------

        kills = real_deaths[
            real_deaths["attacker_name"]
            == player_name
        ].copy()

        # ----------------------------------------------------
        # DEATHS
        # ----------------------------------------------------

        deaths_taken = real_deaths[
            real_deaths["user_name"]
            == player_name
        ].copy()

        # ----------------------------------------------------
        # ASSISTS
        # ----------------------------------------------------

        if "assister_name" in real_deaths.columns:
            assists = real_deaths[
                real_deaths["assister_name"]
                == player_name
            ]
        else:
            assists = pd.DataFrame()

        kill_count = len(kills)
        death_count = len(deaths_taken)
        assist_count = len(assists)

        # ----------------------------------------------------
        # K/D
        # ----------------------------------------------------

        if death_count > 0:
            kd = kill_count / death_count
        else:
            kd = 0

        # ----------------------------------------------------
        # HEADSHOTS
        # ----------------------------------------------------

        if "headshot" in kills.columns:
            headshots = int(
                kills["headshot"]
                .fillna(False)
                .astype(bool)
                .sum()
            )
        else:
            headshots = 0

        if kill_count > 0:
            hs_percent = (
                headshots / kill_count
            ) * 100
        else:
            hs_percent = 0

        # ----------------------------------------------------
        # DAMAGE
        # ----------------------------------------------------

        total_damage = 0

        try:
            damage_events = (
                self.parser.parse_event(
                    "player_hurt"
                )
            )

            if (
                not damage_events.empty
                and "attacker_name"
                in damage_events.columns
                and "dmg_health"
                in damage_events.columns
            ):
                player_damage = damage_events[
                    damage_events["attacker_name"]
                    == player_name
                ]

                total_damage = (
                    pd.to_numeric(
                        player_damage["dmg_health"],
                        errors="coerce"
                    )
                    .fillna(0)
                    .sum()
                )

        except Exception:
            total_damage = 0

        if kill_count > 0:
            average_damage = (
                total_damage / kill_count
            )
        else:
            average_damage = 0

        # ----------------------------------------------------
        # ROUND COUNT
        # ----------------------------------------------------

        total_rounds = 0

        try:
            round_events = (
                self.parser.parse_event(
                    "round_end"
                )
            )

            if not round_events.empty:

                if "is_warmup_period" in round_events.columns:
                    round_events = round_events[
                        round_events[
                            "is_warmup_period"
                        ] != True
                    ]

                if (
                    "total_rounds_played"
                    in round_events.columns
                ):
                    round_numbers = pd.to_numeric(
                        round_events[
                            "total_rounds_played"
                        ],
                        errors="coerce"
                    ).dropna()

                    if not round_numbers.empty:
                        total_rounds = int(
                            round_numbers.max()
                        )

                if total_rounds == 0:
                    total_rounds = len(
                        round_events
                    )

        except Exception:
            total_rounds = 0

        # ----------------------------------------------------
        # UPDATE UI
        # ----------------------------------------------------

        self.stat_cards["kills"].config(
            text=str(kill_count)
        )

        self.stat_cards["deaths"].config(
            text=str(death_count)
        )

        self.stat_cards["assists"].config(
            text=str(assist_count)
        )

        self.stat_cards["kd"].config(
            text=f"{kd:.2f}"
        )

        self.stat_cards["headshots"].config(
            text=str(headshots)
        )

        self.stat_cards["hs_percent"].config(
            text=f"{hs_percent:.1f}%"
        )

        self.stat_cards["damage"].config(
            text=f"{total_damage:.0f}"
        )

        self.stat_cards["avg_damage"].config(
            text=f"{average_damage:.1f}"
        )

        self.round_label.config(
            text=f"Rounds: {total_rounds}"
        )

        self.status_var.set(
            f"Showing statistics for {player_name}"
        )

        # ----------------------------------------------------
        # UPDATE EVENT TABLES
        # ----------------------------------------------------

        self.update_kills_table(kills)
        self.update_deaths_table(deaths_taken)

    # ========================================================
    # KILLS TABLE
    # ========================================================

    def update_kills_table(self, kills):
        for item in self.kills_tree.get_children():
            self.kills_tree.delete(item)

        for _, row in kills.iterrows():

            tick = row.get(
                "tick",
                ""
            )

            victim = row.get(
                "user_name",
                ""
            )

            weapon = row.get(
                "weapon",
                ""
            )

            headshot = row.get(
                "headshot",
                False
            )

            distance = row.get(
                "distance",
                0
            )

            self.kills_tree.insert(
                "",
                "end",
                values=(
                    tick,
                    victim,
                    weapon,
                    "YES" if headshot else "NO",
                    f"{float(distance):.1f}"
                )
            )

    # ========================================================
    # DEATHS TABLE
    # ========================================================

    def update_deaths_table(self, deaths):
        for item in self.deaths_tree.get_children():
            self.deaths_tree.delete(item)

        for _, row in deaths.iterrows():

            tick = row.get(
                "tick",
                ""
            )

            killer = row.get(
                "attacker_name",
                ""
            )

            weapon = row.get(
                "weapon",
                ""
            )

            headshot = row.get(
                "headshot",
                False
            )

            distance = row.get(
                "distance",
                0
            )

            self.deaths_tree.insert(
                "",
                "end",
                values=(
                    tick,
                    killer,
                    weapon,
                    "YES" if headshot else "NO",
                    f"{float(distance):.1f}"
                )
            )


# ============================================================
# START APPLICATION
# ============================================================

if __name__ == "__main__":
    root = tk.Tk()

    app = CS2StatsTracker(root)

    root.mainloop()