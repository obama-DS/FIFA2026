# Audits the master datasets and reports key uniqueness, unmatched records,
# duplicate keys and join match rates between every pair of related tables.

import pandas as pd

from common import export, read_master

RESULTS = []


def add(category, description, status, detail=""):
    row = {"category": category, "check": description, "status": status, "detail": detail}
    RESULTS.append(row)
    print(f"  [{status:6s}] {category:12s} {description}: {detail}")


def ref_rate(series, ref_set, label):
    total = len(series)
    matched = int(series.isin(ref_set).sum())
    rate = matched / total if total else 0.0
    status = "PASS" if rate == 1.0 else "FAIL"
    add("match-rate", label, status, f"{matched}/{total} = {rate:.1%}")
    return rate


def main():
    print("=" * 70)
    print("VALIDATING RELATIONSHIPS BETWEEN MASTER DATASETS")
    print("=" * 70)

    teams = read_master("teams_master.csv")
    aliases = read_master("team_aliases.csv")
    matches = read_master("matches_master.csv")
    odds = read_master("match_odds.csv")
    fixtures = read_master("fixtures_2026_27.csv")
    players = read_master("players_master.csv")
    pstats = read_master("player_season_stats.csv")
    tstats = read_master("team_season_stats.csv")

    team_ids = set(teams["team_id"])
    player_ids = set(players["player_id"])

    # ---- Teams ----
    print("\n[1] Teams")
    add("key", "teams_master team_id unique",
        "PASS" if teams["team_id"].is_unique else "FAIL", f"{len(teams)} teams")
    add("key", "teams_master team_name unique",
        "PASS" if teams["team_name"].is_unique else "FAIL", "")
    alias_ok = aliases["team_id"].isin(team_ids).all()
    add("key", "team_aliases reference valid team_id",
        "PASS" if alias_ok else "FAIL", f"{len(aliases)} aliases")
    alias_canon_ok = True
    for _, r in aliases.iterrows():
        team_name = teams.loc[teams["team_id"] == r["team_id"], "team_name"].iloc[0]
        from common import canonical
        if canonical(r["alias"]) != team_name:
            alias_canon_ok = False
            add("key", "alias -> canonical consistency", "FAIL",
                f"{r['alias']} -> {canonical(r['alias'])} != {team_name}")
    if alias_canon_ok:
        add("key", "alias -> canonical consistency", "PASS", "")
    add("entity", "teams in 2026/27 fixtures", "INFO", f"{int(teams['in_2026_27'].sum())} of {len(teams)}")

    # ---- Matches ----
    print("\n[2] Matches (matches_master + match_odds)")
    add("key", "matches_master match_id unique",
        "PASS" if matches["match_id"].is_unique else "FAIL", f"{len(matches)} matches")
    per_season = matches["season"].value_counts().sort_index()
    counts_ok = (per_season == 380).all()
    add("completeness", "380 matches per season",
        "PASS" if counts_ok else "FAIL", ", ".join(f"{s}:{n}" for s, n in per_season.items()))
    add("key", "match identity (season, date, home, away) unique",
        "PASS" if matches.duplicated(["season", "match_date", "home_team_id", "away_team_id"]).sum() == 0
        else "FAIL", "")
    ref_rate(matches["home_team_id"], team_ids, "matches home_team_id -> teams")
    ref_rate(matches["away_team_id"], team_ids, "matches away_team_id -> teams")
    bad_result = matches[~matches["result"].isin(["H", "D", "A"])]
    add("quality", "result values in {H, D, A}",
        "PASS" if bad_result.empty else "FAIL", f"{len(bad_result)} bad rows")
    bad_goals = matches[(matches[["home_goals", "away_goals"]].lt(0)).any(axis=1)]
    add("quality", "no negative goal counts",
        "PASS" if bad_goals.empty else "FAIL", "")
    odds_ok = odds["match_id"].isin(matches["match_id"]).all()
    add("key", "match_odds match_id references matches",
        "PASS" if odds_ok else "FAIL",
        f"{len(odds)} odds rows, {odds['match_id'].nunique()} matches covered")

    # ---- Fixtures ----
    print("\n[3] Fixtures (2026/27)")
    add("key", "fixtures fixture_id unique",
        "PASS" if fixtures["fixture_id"].is_unique else "FAIL", f"{len(fixtures)} fixtures")
    add("key", "fixtures match_number unique",
        "PASS" if fixtures["match_number"].is_unique else "FAIL", "")
    ref_rate(fixtures["home_team_id"], team_ids, "fixtures home_team_id -> teams")
    ref_rate(fixtures["away_team_id"], team_ids, "fixtures away_team_id -> teams")
    rounds = fixtures["round_number"].value_counts().sort_index()
    rounds_ok = (rounds == 10).all() and set(rounds.index) == set(range(1, 39))
    add("completeness", "38 rounds x 10 fixtures",
        "PASS" if rounds_ok else "FAIL", "")

    # ---- Players ----
    print("\n[4] Players")
    add("key", "players_master player_id unique",
        "PASS" if players["player_id"].is_unique else "FAIL", f"{len(players)} players")
    dup_names = players[players.duplicated("player_name", keep=False)]
    add("quality", "player names unique (limitation: no stable ID)",
        "WARN" if len(dup_names) else "PASS", f"{len(dup_names)} rows share a name")
    ref_rate(players["team_id"], team_ids, "players team_id -> teams")
    ref_rate(pstats["player_id"], player_ids, "player_season_stats player_id -> players_master")
    add("key", "player_season_stats (player_id, season) unique",
        "PASS" if pstats.duplicated(["player_id", "season"]).sum() == 0 else "FAIL",
        f"{len(pstats)} player-seasons, seasons={sorted(pstats['season'].unique())}")
    ref_rate(pstats["team_id"], team_ids, "player_season_stats team_id -> teams")

    # ---- Team-season stats ----
    print("\n[5] Team-season stats")
    add("key", "team_season_stats (team_id, season) unique",
        "PASS" if tstats.duplicated(["team_id", "season"]).sum() == 0 else "FAIL",
        f"{len(tstats)} team-seasons")
    ref_rate(tstats["team_id"], team_ids, "team_season_stats team_id -> teams")
    bad_points = tstats[tstats["points"] != 3 * tstats["wins"] + tstats["draws"]]
    add("quality", "points == 3*wins + draws",
        "PASS" if bad_points.empty else "FAIL", f"{len(bad_points)} bad rows")
    bad_mp = tstats[tstats["mp"] != tstats["wins"] + tstats["draws"] + tstats["losses"]]
    add("quality", "mp == wins + draws + losses",
        "PASS" if bad_mp.empty else "FAIL", "")
    not_full = tstats[tstats["mp"] != 38]
    add("completeness", "each team-season has 38 games",
        "PASS" if not_full.empty else "FAIL",
        f"{len(not_full)} rows with mp != 38" if not not_full.empty else "all 38")

    # ---- Cross-dataset match rates (summary) ----
    print("\n[6] Cross-dataset match rates")
    ref_rate(matches["home_team_id"], team_ids, "matches -> teams")
    ref_rate(fixtures["home_team_id"], team_ids, "fixtures -> teams")
    ref_rate(fixtures["away_team_id"], team_ids, "fixtures -> teams (away)")
    ref_rate(players["team_id"], team_ids, "players -> teams")
    ref_rate(pstats["team_id"], team_ids, "player-season stats -> teams")

    no_matches = teams[~teams["team_id"].isin(set(matches["home_team_id"]) | set(matches["away_team_id"]))]
    add("entity", "teams with no match rows in 2018/19-2025/26",
        "INFO", ", ".join(no_matches["team_name"]) if not no_matches.empty else "none")
    no_players = teams[~teams["team_id"].isin(set(players["team_id"]))]
    add("entity", "teams with no player rows (2025/26)",
        "INFO", ", ".join(no_players["team_name"]) if not no_players.empty else "none")

    df = pd.DataFrame(RESULTS)
    export(df, "validation_results.csv")
    fails = df[df["status"] == "FAIL"]
    print("\n" + "=" * 70)
    print(f"VALIDATION SUMMARY: {len(df)} checks, {len(fails)} FAILED, "
          f"{len(df[df['status'] == 'WARN'])} WARNINGS")
    print("=" * 70)


if __name__ == "__main__":
    main()
