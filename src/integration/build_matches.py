# Builds matches_master.csv, match_odds.csv, fixtures_2026_27.csv and
# team_season_stats.csv from the raw E0 match files and the fixture list.

import numpy as np
import pandas as pd

from common import (MASTER_DIR, MATCH_FILES, RAW_FIXTURES, canonical, check_unique,
                    export, load_raw, map_names, read_master)

CORE_COLS = [
    "Div", "Date", "Time", "HomeTeam", "AwayTeam",
    "FTHG", "FTAG", "FTR", "HTHG", "HTAG", "HTR", "Referee",
    "HS", "AS", "HST", "AST", "HF", "AF", "HC", "AC", "HY", "AY", "HR", "AR",
]


def team_lookup():
    teams = read_master("teams_master.csv")
    return dict(zip(teams["team_name"], teams["team_id"])), teams


def build_matches(team_map):
    print("Building matches_master from E0 files...")
    frames = []
    odds_frames = []
    for fname, season in MATCH_FILES.items():
        raw = load_raw(fname)
        core = [c for c in CORE_COLS if c in raw.columns]
        df = raw[core].copy()
        df["_season"] = season
        df["_row"] = np.arange(len(df))
        odds = raw[[c for c in raw.columns if c not in CORE_COLS]].copy()
        odds["_season"] = season
        odds["_row"] = np.arange(len(odds))
        frames.append(df)
        odds_frames.append(odds)
        print(f"  {fname}: {len(df)} matches ({season})")

    matches = pd.concat(frames, ignore_index=True)
    odds_all = pd.concat(odds_frames, ignore_index=True)

    matches["match_date"] = pd.to_datetime(matches["Date"], format="%d/%m/%Y", errors="coerce")
    matches["season_start"] = matches["_season"].str[:4].astype(int)
    matches = matches.sort_values(["season_start", "match_date", "_row"]).reset_index(drop=True)
    matches["match_id"] = np.arange(1, len(matches) + 1)

    odds_all = odds_all.merge(matches[["_season", "_row", "match_id"]], on=["_season", "_row"], how="left")
    odds_all = odds_all.drop(columns=["_season", "_row"])
    odds_all = odds_all[["match_id"] + [c for c in odds_all.columns if c != "match_id"]]
    odds_all = odds_all.sort_values("match_id").reset_index(drop=True)
    print(f"  odds rows with no match_id: {int(odds_all['match_id'].isna().sum())}")

    matches["home_team_name"] = matches["HomeTeam"].map(canonical)
    matches["away_team_name"] = matches["AwayTeam"].map(canonical)
    matches["home_team_id"] = map_names(matches["home_team_name"], team_map, "home teams")
    matches["away_team_id"] = map_names(matches["away_team_name"], team_map, "away teams")

    kickoff_time = (matches["Time"].astype(object)
                    if "Time" in matches.columns
                    else pd.Series(pd.NA, index=matches.index))

    out = pd.DataFrame({
        "match_id": matches["match_id"],
        "season": matches["_season"],
        "match_date": matches["match_date"],
        "kickoff_time": kickoff_time,
        "division": matches["Div"],
        "home_team_id": matches["home_team_id"],
        "away_team_id": matches["away_team_id"],
        "home_team_name": matches["home_team_name"],
        "away_team_name": matches["away_team_name"],
        "home_goals": matches["FTHG"],
        "away_goals": matches["FTAG"],
        "result": matches["FTR"],
        "ht_home_goals": matches["HTHG"],
        "ht_away_goals": matches["HTAG"],
        "ht_result": matches["HTR"],
        "referee": matches["Referee"],
        "home_shots": matches["HS"],
        "away_shots": matches["AS"],
        "home_shots_on_target": matches["HST"],
        "away_shots_on_target": matches["AST"],
        "home_fouls": matches["HF"],
        "away_fouls": matches["AF"],
        "home_corners": matches["HC"],
        "away_corners": matches["AC"],
        "home_yellows": matches["HY"],
        "away_yellows": matches["AY"],
        "home_reds": matches["HR"],
        "away_reds": matches["AR"],
    })

    check_unique(out, ["match_id"], "matches_master.match_id")
    check_unique(out, ["season", "match_date", "home_team_id", "away_team_id"], "match identity")
    export(out, "matches_master.csv")
    export(odds_all, "match_odds.csv")
    return out


def build_fixtures(team_map):
    print("\nBuilding fixtures_2026_27 from the 2026/27 fixture list...")
    fix = load_raw(RAW_FIXTURES).copy()
    fix["home_team_name"] = fix["Home Team"].map(canonical)
    fix["away_team_name"] = fix["Away Team"].map(canonical)
    fix["home_team_id"] = map_names(fix["home_team_name"], team_map, "fixture home teams")
    fix["away_team_id"] = map_names(fix["away_team_name"], team_map, "fixture away teams")
    fix["kickoff"] = pd.to_datetime(fix["Date"], format="%d/%m/%Y %H:%M", errors="coerce")
    fix["fixture_id"] = np.arange(1, len(fix) + 1)

    out = pd.DataFrame({
        "fixture_id": fix["fixture_id"],
        "match_number": fix["Match Number"],
        "round_number": fix["Round Number"],
        "season": "2026/27",
        "kickoff": fix["kickoff"],
        "kickoff_text": fix["Date"],
        "stadium": fix["Location"],
        "home_team_id": fix["home_team_id"],
        "away_team_id": fix["away_team_id"],
        "home_team_name": fix["home_team_name"],
        "away_team_name": fix["away_team_name"],
        "result": fix["Result"],
    })
    check_unique(out, ["fixture_id"], "fixtures.fixture_id")
    check_unique(out, ["match_number"], "fixtures.match_number")
    export(out, "fixtures_2026_27.csv")
    return out


def build_team_season_stats(matches, teams):
    print("\nBuilding team_season_stats by aggregating matches_master...")
    team_name = dict(zip(teams["team_id"], teams["team_name"]))

    def team_rows(venue, home_ids, away_ids, gf, ga, wmask, dmask, lmask,
                  sh, sa, sot, sota, fouls, foulsa, corners, cornersa,
                  yellows, yellowsa, reds, redsa):
        return pd.DataFrame({
            "season": matches["season"],
            "team_id": home_ids,
            "venue": venue,
            "gf": gf, "ga": ga,
            "w": wmask, "d": dmask, "l": lmask,
            "sh": sh, "sa": sa,
            "sot": sot, "sota": sota,
            "fouls": fouls, "foulsa": foulsa,
            "corners": corners, "cornersa": cornersa,
            "yellows": yellows, "yellowsa": yellowsa,
            "reds": reds, "redsa": redsa,
        })

    home = team_rows(
        "home",
        matches["home_team_id"], matches["away_team_id"],
        matches["home_goals"], matches["away_goals"],
        matches["result"].eq("H").astype(int), matches["result"].eq("D").astype(int),
        matches["result"].eq("A").astype(int),
        matches["home_shots"], matches["away_shots"],
        matches["home_shots_on_target"], matches["away_shots_on_target"],
        matches["home_fouls"], matches["away_fouls"],
        matches["home_corners"], matches["away_corners"],
        matches["home_yellows"], matches["away_yellows"],
        matches["home_reds"], matches["away_reds"],
    )
    away = team_rows(
        "away",
        matches["away_team_id"], matches["home_team_id"],
        matches["away_goals"], matches["home_goals"],
        matches["result"].eq("A").astype(int), matches["result"].eq("D").astype(int),
        matches["result"].eq("H").astype(int),
        matches["away_shots"], matches["home_shots"],
        matches["away_shots_on_target"], matches["home_shots_on_target"],
        matches["away_fouls"], matches["home_fouls"],
        matches["away_corners"], matches["home_corners"],
        matches["away_yellows"], matches["home_yellows"],
        matches["away_reds"], matches["home_reds"],
    )
    comb = pd.concat([home, away], ignore_index=True)

    base = comb.groupby(["season", "team_id"], as_index=False).agg(
        mp=("gf", "count"),
        wins=("w", "sum"), draws=("d", "sum"), losses=("l", "sum"),
        goals_for=("gf", "sum"), goals_against=("ga", "sum"),
        clean_sheets=("ga", lambda s: (s == 0).sum()),
        failed_to_score=("gf", lambda s: (s == 0).sum()),
        shots_for=("sh", "sum"), shots_against=("sa", "sum"),
        sot_for=("sot", "sum"), sot_against=("sota", "sum"),
        fouls_for=("fouls", "sum"), fouls_against=("foulsa", "sum"),
        corners_for=("corners", "sum"), corners_against=("cornersa", "sum"),
        yellows_for=("yellows", "sum"), yellows_against=("yellowsa", "sum"),
        reds_for=("reds", "sum"), reds_against=("redsa", "sum"),
    )
    h = comb[comb["venue"] == "home"].groupby(["season", "team_id"], as_index=False).agg(
        home_mp=("gf", "count"), home_wins=("w", "sum"), home_draws=("d", "sum"),
        home_losses=("l", "sum"), home_goals_for=("gf", "sum"), home_goals_against=("ga", "sum"))
    a = comb[comb["venue"] == "away"].groupby(["season", "team_id"], as_index=False).agg(
        away_mp=("gf", "count"), away_wins=("w", "sum"), away_draws=("d", "sum"),
        away_losses=("l", "sum"), away_goals_for=("gf", "sum"), away_goals_against=("ga", "sum"))

    stats = base.merge(h, on=["season", "team_id"]).merge(a, on=["season", "team_id"])
    stats["points"] = 3 * stats["wins"] + stats["draws"]
    stats["goal_difference"] = stats["goals_for"] - stats["goals_against"]
    stats["ppg"] = stats["points"] / stats["mp"]
    stats["win_rate"] = stats["wins"] / stats["mp"]
    stats["draw_rate"] = stats["draws"] / stats["mp"]
    stats["loss_rate"] = stats["losses"] / stats["mp"]
    stats["avg_goals_for"] = stats["goals_for"] / stats["mp"]
    stats["avg_goals_against"] = stats["goals_against"] / stats["mp"]
    stats["avg_goal_difference"] = stats["goal_difference"] / stats["mp"]
    stats["team_name"] = stats["team_id"].map(team_name)

    order = ["team_id", "team_name", "season", "mp", "wins", "draws", "losses", "points",
             "goals_for", "goals_against", "goal_difference", "clean_sheets", "failed_to_score",
             "home_mp", "home_wins", "home_draws", "home_losses", "home_goals_for", "home_goals_against",
             "away_mp", "away_wins", "away_draws", "away_losses", "away_goals_for", "away_goals_against",
             "shots_for", "shots_against", "sot_for", "sot_against",
             "fouls_for", "fouls_against", "corners_for", "corners_against",
             "yellows_for", "yellows_against", "reds_for", "reds_against",
             "ppg", "win_rate", "draw_rate", "loss_rate",
             "avg_goals_for", "avg_goals_against", "avg_goal_difference"]
    stats = stats[order]
    stats = stats.sort_values(["season", "points"], ascending=[True, False]).reset_index(drop=True)
    check_unique(stats, ["team_id", "season"], "team_season_stats (team_id, season)")
    export(stats, "team_season_stats.csv")


def main():
    team_map, teams = team_lookup()
    matches = build_matches(team_map)
    build_fixtures(team_map)
    build_team_season_stats(matches, teams)


if __name__ == "__main__":
    main()
