# Builds teams_master.csv and team_aliases.csv.
# Team entities come from three sources: E0 match files (HomeTeam/AwayTeam),
# the player file (Squad), and the 2026/27 fixture list (Home/Away Team).

import pandas as pd

from common import (EPL_COMP, MASTER_DIR, MATCH_FILES, RAW_FIXTURES, RAW_PLAYERS,
                    canonical, export, full_name, load_raw)


def collect_team_sources():
    sources = {}
    for fname, season in MATCH_FILES.items():
        df = load_raw(fname)
        for col in ("HomeTeam", "AwayTeam"):
            for name in df[col].dropna().unique():
                key = str(name).strip()
                info = sources.setdefault(key, {"e0_seasons": set(), "sources": set()})
                info["e0_seasons"].add(season)
                info["sources"].add("E0")

    players = load_raw(RAW_PLAYERS)
    epl = players[players["Comp"] == EPL_COMP]
    for name in epl["Squad"].dropna().unique():
        key = str(name).strip()
        sources.setdefault(key, {"e0_seasons": set(), "sources": set()})["sources"].add("players")

    fixtures = load_raw(RAW_FIXTURES)
    for col in ("Home Team", "Away Team"):
        for name in fixtures[col].dropna().unique():
            key = str(name).strip()
            sources.setdefault(key, {"e0_seasons": set(), "sources": set()})["sources"].add("fixtures")
    return sources


def build():
    print("Building teams_master from raw team-name sources...")
    sources = collect_team_sources()
    print(f"  distinct raw team names found: {len(sources)}")

    fixtures = load_raw(RAW_FIXTURES)
    fixture_team_names = set()
    for col in ("Home Team", "Away Team"):
        fixture_team_names.update(str(n).strip() for n in fixtures[col].dropna().unique())
    fixture_canonical = {canonical(n) for n in fixture_team_names}

    canon_to_id = {}
    canon_e0_seasons = {}
    team_rows = []
    alias_rows = []
    for raw_name, info in sources.items():
        cname = canonical(raw_name)
        canon_e0_seasons.setdefault(cname, set()).update(info["e0_seasons"])

    for cname in sorted(canon_e0_seasons):
        team_id = len(team_rows) + 1
        canon_to_id[cname] = team_id
        e0 = sorted(canon_e0_seasons[cname])
        team_rows.append({
            "team_id": team_id,
            "team_name": cname,
            "team_full_name": full_name(cname),
            "home_stadium": None,
            "in_2026_27": cname in fixture_canonical,
            "first_season": e0[0] if e0 else None,
            "last_season": e0[-1] if e0 else None,
            "n_seasons": len(e0),
        })

    for raw_name, info in sources.items():
        alias_rows.append({
            "team_id": canon_to_id[canonical(raw_name)],
            "alias": raw_name,
            "source": ",".join(sorted(info["sources"])),
        })

    teams = pd.DataFrame(team_rows)
    stadium_map = {}
    for _, row in fixtures.drop_duplicates("Home Team").iterrows():
        stadium_map[canonical(row["Home Team"])] = row["Location"]
    teams["home_stadium"] = teams["team_name"].map(stadium_map)

    aliases = pd.DataFrame(alias_rows)
    aliases = aliases.sort_values(["team_id", "alias"]).reset_index(drop=True)

    export(teams, "teams_master.csv")
    export(aliases, "team_aliases.csv")

    print(f"  teams: {len(teams)} | in 2026/27 fixtures: {int(teams['in_2026_27'].sum())}")
    print(f"  aliases: {len(aliases)}")


if __name__ == "__main__":
    build()
