import tkinter as tk
from tkinter import ttk

from database.database import Database


class Dashboard:
    def __init__(self, root):
        self.root = root

        self.root.title("CS2 Stats Tracker")
        self.root.geometry("1150x800")
        self.root.minsize(950, 650)

        self.database = Database()

        self.setup_style()
        self.create_ui()

        self.load_players()

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

    # ========================================================
    # UI
    # ========================================================

    def create_ui(self):
        self.root.configure(bg="#111318")

        self.main = ttk.Frame(
            self.root,
            padding=25
        )

        self.main.pack(
            fill="both",
            expand=True
        )

        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        ttk.Label(
            self.main,
            text="CS2 STATS TRACKER",
            style="Title.TLabel"
        ).pack(anchor="w")

        ttk.Label(
            self.main,
            text="Your Counter-Strike performance history",
            style="Subtitle.TLabel"
        ).pack(
            anchor="w",
            pady=(0, 20)
        )

        # ----------------------------------------------------
        # PLAYER SELECTOR
        # ----------------------------------------------------

        selector = ttk.Frame(
            self.main,
            style="Card.TFrame",
            padding=15
        )

        selector.pack(
            fill="x",
            pady=(0, 20)
        )

        ttk.Label(
            selector,
            text="PLAYER"
        ).pack(side="left")

        self.player_var = tk.StringVar()

        self.player_combo = ttk.Combobox(
            selector,
            textvariable=self.player_var,
            state="readonly",
            width=35
        )

        self.player_combo.pack(
            side="left",
            padx=15
        )

        self.player_combo.bind(
            "<<ComboboxSelected>>",
            self.player_changed
        )

        # ----------------------------------------------------
        # OVERALL
        # ----------------------------------------------------

        ttk.Label(
            self.main,
            text="OVERALL PERFORMANCE"
        ).pack(
            anchor="w",
            pady=(0, 8)
        )

        self.stats_frame = ttk.Frame(
            self.main
        )

        self.stats_frame.pack(
            fill="x",
            pady=(0, 20)
        )

        self.stat_cards = {}

        stats = [
            ("Matches", "matches"),
            ("K/D", "kd"),
            ("Kills", "kills"),
            ("Deaths", "deaths"),
            ("Assists", "assists"),
            ("HS %", "hs"),
            ("Damage", "damage")
        ]

        for title, key in stats:

            card = ttk.Frame(
                self.stats_frame,
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

            value.pack(
                pady=(5, 0)
            )

            self.stat_cards[key] = value

        # ----------------------------------------------------
        # MATCH HISTORY
        # ----------------------------------------------------

        ttk.Label(
            self.main,
            text="MATCH HISTORY"
        ).pack(
            anchor="w",
            pady=(0, 8)
        )

        # Scrollable canvas
        history_container = ttk.Frame(
            self.main
        )

        history_container.pack(
            fill="both",
            expand=True
        )

        self.canvas = tk.Canvas(
            history_container,
            bg="#111318",
            highlightthickness=0
        )

        scrollbar = ttk.Scrollbar(
            history_container,
            orient="vertical",
            command=self.canvas.yview
        )

        self.history_frame = ttk.Frame(
            self.canvas
        )

        self.history_window = (
            self.canvas.create_window(
                (0, 0),
                window=self.history_frame,
                anchor="nw"
            )
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.history_frame.bind(
            "<Configure>",
            self.update_scroll_region
        )

        self.canvas.bind(
            "<Configure>",
            self.resize_history
        )

    # ========================================================
    # PLAYER LIST
    # ========================================================

    def load_players(self):

        matches = self.database.get_matches()

        players = set()

        for match in matches:

            match_id = match[0]

            # Get players belonging to this match
            cursor = self.database.connection.cursor()

            cursor.execute(
                """
                SELECT DISTINCT player_name
                FROM player_stats
                WHERE match_id = ?
                """,
                (match_id,)
            )

            results = cursor.fetchall()

            for row in results:
                players.add(row[0])

        players = sorted(players)

        self.player_combo["values"] = players

        if players:

            self.player_var.set(
                players[0]
            )

            self.update_dashboard()

    # ========================================================
    # PLAYER CHANGED
    # ========================================================

    def player_changed(self, event=None):
        self.update_dashboard()

    # ========================================================
    # UPDATE DASHBOARD
    # ========================================================

    def update_dashboard(self):

        player = self.player_var.get()

        if not player:
            return

        overall = (
            self.database.get_overall_stats(
                player
            )
        )

        if overall is None:
            return

        # ----------------------------------------------------
        # Overall cards
        # ----------------------------------------------------

        self.stat_cards["matches"].config(
            text=str(
                overall["matches"]
            )
        )

        self.stat_cards["kills"].config(
            text=str(
                overall["kills"]
            )
        )

        self.stat_cards["deaths"].config(
            text=str(
                overall["deaths"]
            )
        )

        self.stat_cards["assists"].config(
            text=str(
                overall["assists"]
            )
        )

        self.stat_cards["kd"].config(
            text=f"{overall['average_kd']:.2f}"
        )

        self.stat_cards["hs"].config(
            text=f"{overall['average_hs_percentage']:.1f}%"
        )

        self.stat_cards["damage"].config(
            text=f"{overall['damage']:.0f}"
        )

        # ----------------------------------------------------
        # Match history
        # ----------------------------------------------------

        self.clear_history()

        matches = (
            self.database.get_player_matches(
                player
            )
        )

        for match in matches:
            self.create_match_card(match)

    # ========================================================
    # CLEAR HISTORY
    # ========================================================

    def clear_history(self):

        for widget in self.history_frame.winfo_children():
            widget.destroy()

    # ========================================================
    # MATCH CARD
    # ========================================================

    def create_match_card(self, match):

        (
            match_id,
            demo_filename,
            map_name,
            rounds,
            kills,
            deaths,
            assists,
            kd,
            headshots,
            hs_percentage,
            damage,
            average_damage,
            created_at
        ) = match

        # ----------------------------------------------------
        # Card
        # ----------------------------------------------------

        card = tk.Frame(
            self.history_frame,
            bg="#1A1D23",
            bd=0
        )

        card.pack(
            fill="x",
            pady=5,
            padx=3
        )

        # ----------------------------------------------------
        # Header
        # ----------------------------------------------------

        header = tk.Frame(
            card,
            bg="#1A1D23",
            cursor="hand2"
        )

        header.pack(
            fill="x"
        )

        arrow = tk.Label(
            header,
            text="▶",
            bg="#1A1D23",
            fg="#8F96A3",
            font=("Segoe UI", 11)
        )

        arrow.pack(
            side="left",
            padx=(15, 8),
            pady=14
        )

        map_label = tk.Label(
            header,
            text=map_name or "Unknown",
            bg="#1A1D23",
            fg="#FFFFFF",
            font=("Segoe UI", 11, "bold")
        )

        map_label.pack(
            side="left",
            pady=14
        )

        score_label = tk.Label(
            header,
            text=f"{kills} / {assists} / {deaths}",
            bg="#1A1D23",
            fg="#FFFFFF",
            font=("Segoe UI", 10, "bold")
        )

        score_label.pack(
            side="right",
            padx=15
        )

        kd_label = tk.Label(
            header,
            text=f"K/D {kd:.2f}",
            bg="#1A1D23",
            fg="#8F96A3",
            font=("Segoe UI", 9)
        )

        kd_label.pack(
            side="right",
            padx=10
        )

        # ----------------------------------------------------
        # Details
        # ----------------------------------------------------

        details = tk.Frame(
            card,
            bg="#15181D"
        )

        details.pack(
            fill="x"
        )

        details.pack_forget()

        # Details grid
        detail_values = [
            ("Rounds", rounds),
            ("Headshots", headshots),
            ("HS %", f"{hs_percentage:.1f}%"),
            ("Damage", f"{damage:.0f}"),
            (
                "Avg Damage/Kill",
                f"{average_damage:.1f}"
            )
        ]

        for index, (title, value) in enumerate(
            detail_values
        ):

            block = tk.Frame(
                details,
                bg="#15181D"
            )

            block.grid(
                row=0,
                column=index,
                padx=20,
                pady=15
            )

            tk.Label(
                block,
                text=title,
                bg="#15181D",
                fg="#7F8794",
                font=("Segoe UI", 8)
            ).pack()

            tk.Label(
                block,
                text=str(value),
                bg="#15181D",
                fg="#FFFFFF",
                font=("Segoe UI", 11, "bold")
            ).pack(
                pady=(3, 0)
            )

        # ----------------------------------------------------
        # Expand / collapse
        # ----------------------------------------------------

        expanded = False

        def toggle():

            nonlocal expanded

            if expanded:

                details.pack_forget()
                arrow.config(text="▶")

                expanded = False

            else:

                details.pack(
                    fill="x"
                )

                arrow.config(text="▼")

                expanded = True

            self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )

        # Make entire header clickable
        for widget in (
            header,
            arrow,
            map_label,
            score_label,
            kd_label
        ):
            widget.bind(
                "<Button-1>",
                lambda event: toggle()
            )

    # ========================================================
    # SCROLLING
    # ========================================================

    def update_scroll_region(self, event=None):

        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def resize_history(self, event):

        self.canvas.itemconfig(
            self.history_window,
            width=event.width
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.database.close()
        self.root.destroy()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = Dashboard(root)

    root.protocol(
        "WM_DELETE_WINDOW",
        app.close
    )

    root.mainloop()