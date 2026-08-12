# Builds players_master.csv and player_season_stats.csv from the 2025/26
# FBref player file. Only Premier League players (Comp == eng Premier League)
# are kept; non-EPL leagues are out of scope and are counted, not silently lost.

import numpy as np
import pandas as pd

from common import (EPL_COMP, RAW_PLAYERS, canonical, check_unique, export,
                    load_raw, map_names, read_master)


def build():
    print("Building players_master and player_season_stats...")
    teams = read_master("teams_master.csv")
    team_map = dict(zip(teams["team_name"], teams["team_id"]))

    raw = load_raw(RAW_PLAYERS)
    epl = raw[raw["Comp"] == EPL_COMP].copy()
    print(f"  players file rows: {len(raw)} | EPL rows kept: {len(epl)} | non-EPL excluded: {len(raw) - len(epl)}")

    epl["team_name"] = epl["Squad"].map(canonical)
    epl["team_id"] = map_names(epl["team_name"], team_map, "player squads -> teams")
    epl = epl.sort_values(["team_name", "Player"]).reset_index(drop=True)
    epl["player_id"] = np.arange(1, len(epl) + 1)

    master = pd.DataFrame({
        "player_id": epl["player_id"],
        "player_name": epl["Player"],
        "nation": epl["Nation"],
        "birth_year": epl["Born"],
        "position": epl["Pos"],
        "primary_position": epl["Pos"].str.split(",").str[0].str.strip(),
        "team_id": epl["team_id"],
        "team_name": epl["team_name"],
        "comp": epl["Comp"],
    })
    check_unique(master, ["player_id"], "players_master.player_id")
    dup_names = master[master.duplicated("player_name", keep=False)]
    print(f"  players with a name shared by another player: {len(dup_names)}")

    export(master, "players_master.csv")

    drop_cols = {"Rk", "Player", "Nation", "Pos", "Squad", "Comp", "Born",
                 "team_name", "team_id", "player_id"}
    stats_cols = [c for c in epl.columns if c not in drop_cols]
    stats = epl[["player_id", "team_id"] + stats_cols].copy()
    stats.insert(1, "season", "2025/26")
    check_unique(stats, ["player_id", "season"], "player_season_stats (player_id, season)")
    export(stats, "player_season_stats.csv")


if __name__ == "__main__":
    build()
