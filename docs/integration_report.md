# Integration Report

How the raw datasets were connected into logical master datasets in `data/master/`.
Raw source files were never modified.

---

## 1. Pipeline overview

Run order (each script is idempotent and rebuilds its outputs from scratch):

```text
1. python src/integration/build_teams.py          -> teams_master, team_aliases
2. python src/integration/build_matches.py        -> matches_master, match_odds, fixtures_2026_27, team_season_stats
3. python src/integration/build_players.py        -> players_master, player_season_stats
4. python src/integration/validate_relationships.py -> validation_results (audit)
```

Shared helpers in `src/integration/common.py`:
- `canonical(name)` / `full_name(name)` — team-name normalisation.
- `load_raw`, `read_master`, `export` — read/write helpers (raw files opened read-only).
- `check_unique(df, keys, label)` — duplicate-key detection.
- `map_names(series, lookup, label)` — name->id mapping with unmatched-record reporting.
- `merge_checked(...)` — merge that reports matched / left-only / right-only rows.

---

## 2. Source files used

| Source file | Used for | Notes |
|---|---|---|
| `E0 (8).csv` | 2018/19 matches | `E0 (7).csv` was an exact MD5 duplicate; not included |
| `E0 (6).csv` .. `E0 (1).csv`, `E0.csv` | 2019/20 .. 2025/26 matches | Same schema family; only bookmaker-odds columns vary |
| `players_data_light-2025_2026.csv` | player entities + 2025/26 player stats | 1986 rows total; only `eng Premier League` kept (404); 1582 non-EPL rows excluded and counted |
| `epl-2026-GMTStandardTime.csv` | 2026/27 fixtures | 380 fixtures; `Result` empty (prediction target) |
| `E3.csv`, `logs_0.csv` | Not used | `E3.csv` = 1997/98 League Two (out of scope); `logs_0.csv` = system log |

---

## 3. Teams — `teams_master.csv` + `team_aliases.csv`

**Source of team names:** the union of `HomeTeam`/`AwayTeam` across all 8 E0 files, the `Squad`
column of the player file (EPL rows), and `Home Team`/`Away Team` in the fixture list.
This produced **39 distinct raw spellings**, which were resolved to **32 canonical teams**.

**Resolution rule:** a team exists once per canonical name; every raw spelling is retained in
`team_aliases.csv` (many-to-one: alias -> team_id). Nothing was dropped.

Examples of raw -> canonical:

| Raw spelling (seen in) | Canonical `team_name` |
|---|---|
| `Man Utd` (fixtures), `Manchester Utd` (players), `Man United` (E0) | `Man United` |
| `Spurs` (fixtures), `Tottenham` (E0/players) | `Tottenham` |
| `Nott'ham Forest` (players), `Nott'm Forest` (E0/fixtures) | `Nott'm Forest` |
| `Leeds United` (players), `Leeds` (E0) | `Leeds` |
| `Newcastle Utd` (players), `Newcastle` (E0) | `Newcastle` |
| `Manchester City` (players), `Man City` (E0) | `Man City` |

**`teams_master.csv` — 32 rows:** `team_id`, `team_name`, `team_full_name`, `home_stadium`,
`in_2026_27`, `first_season`, `last_season`, `n_seasons`.

- `team_full_name` from `NAME_OVERRIDES`; `home_stadium` from the fixture `Location` for the
  20 teams in 2026/27 (e.g. Arsenal -> Emirates Stadium), `NULL` otherwise.
- `first_season`/`last_season`/`n_seasons` are computed by aggregating the season labels of
  **all** aliases for the canonical team (handles `Spurs`->`Tottenham` etc.).
- 20 of 32 teams are in the 2026/27 fixtures; the other 12 appear only in the historical
  window (relegated/promoted clubs).

**`team_aliases.csv` — 39 rows:** `team_id`, `alias`, `source` (comma-separated).

---

## 4. Matches — `matches_master.csv` + `match_odds.csv`

**How it was built.** Each E0 file is read with its season label (mapping in `common.py`).
Core match columns are kept in `matches_master`; **all bookmaker odds columns are moved**
(unmodified, 1:1 by `match_id`) into `match_odds.csv` so betting odds stay out of the modelling
tables but are not lost. `HomeTeam`/`AwayTeam` are mapped to `team_id` through `teams_master`
(0 unmatched across 3040 rows).

**`matches_master.csv` — 3040 rows (8 seasons x 380):** `match_id`, `season`, `match_date`,
`kickoff_time`, `division`, `home_team_id`, `away_team_id`, `home_team_name`, `away_team_name`,
`home_goals`, `away_goals`, `result`, `ht_home_goals`, `ht_away_goals`, `ht_result`, `referee`,
`home_shots`, `away_shots`, `home_shots_on_target`, `away_shots_on_target`, `home_fouls`,
`away_fouls`, `home_corners`, `away_corners`, `home_yellows`, `away_yellows`, `home_reds`,
`away_reds`.

- Natural key for duplicate detection: `(season, match_date, home_team_id, away_team_id)`.
- `division` always `E0` (Premier League), kept for lineage.
- `kickoff_time` is `NULL` for 2018/19 (that file has no `Time` column).

**`match_odds.csv` — 3040 rows:** `match_id` + raw bookmaker columns (B365, BWin, IW, PS, WH,
VCS, Max, Avg).

---

## 5. Fixtures — `fixtures_2026_27.csv`

**How it was built.** Raw fixture list normalised and mapped to `team_id` (0 unmatched).
`Match Number` / `Round Number` kept as-is; `season = 2026/27`; `Result` stays empty (the
forecast target).

**`fixtures_2026_27.csv` — 380 rows (38 rounds x 10):** `fixture_id`, `match_number`,
`round_number`, `season`, `kickoff`, `kickoff_text`, `stadium`, `home_team_id`, `away_team_id`,
`home_team_name`, `away_team_name`, `result`.

---

## 6. Team-season stats — `team_season_stats.csv`

**How it was built.** Derived purely by aggregating `matches_master` (no invented data).
Each match contributes one row to its home team and one row to its away team; grouped by
`(season, team_id)`.

**`team_season_stats.csv` — 160 rows (8 seasons x 20 teams):** `team_id`, `team_name`, `season`,
`mp`, `wins`, `draws`, `losses`, `points`, `goals_for`, `goals_against`, `goal_difference`,
`clean_sheets`, `failed_to_score`, home/away splits (`home_mp` .. `away_goals_against`),
per-90-ish rates (`ppg`, `win_rate`, `draw_rate`, `loss_rate`, `avg_goals_for`,
`avg_goals_against`, `avg_goal_difference`), and shot/foul/corner/card aggregates.

Cardinality: teams 1 -> many team-season rows via `team_id`.

---

## 7. Players — `players_master.csv` + `player_season_stats.csv`

**How it was built.** Player file filtered to `eng Premier League` (404 of 1986 rows; the
1582 non-EPL rows are out of scope, counted not silently dropped). Each player's `Squad` was
mapped to `team_id` (0 unmatched). Because the source has **no stable player ID**, `player_id`
is assigned per `(Squad, Player)` snapshot row.

**`players_master.csv` — 404 rows (identity):** `player_id`, `player_name`, `nation`,
`birth_year`, `position`, `primary_position`, `team_id`, `team_name`, `comp`.

**`player_season_stats.csv` — 404 rows (one player-season, `season = 2025/26`):**
`player_id`, `season`, `team_id`, `Age`, then all FBref stat columns. Identity columns
(`Player`, `Nation`, `Pos`, `Squad`, `Comp`, `Born`) and file-local `Rk` were removed from the
stats table — they live in `players_master`.

Cardinalities: players 1 -> many player-season rows via `player_id`; teams 1 -> many players
via `team_id`.

---

## 8. Relationship validation — `validate_relationships.py`

Audits key uniqueness, duplicate keys, unmatched records and match rates, and writes
`data/master/validation_results.csv`.

**Result: 36 checks — 35 PASS, 0 FAIL, 1 WARN.**

| Check | Status | Detail |
|---|---|---|
| teams_master `team_id` / `team_name` unique | PASS | 32 teams |
| team_aliases reference valid `team_id` | PASS | 39 aliases |
| matches `match_id` unique | PASS | 3040 |
| 380 matches per season (8 seasons) | PASS | 2018/19..2025/26 |
| match identity `(season,date,home,away)` unique | PASS | |
| result values in {H,D,A}; no negative goals | PASS | 0 bad rows |
| match_odds 1:1 with matches | PASS | 3040/3040 |
| fixtures `fixture_id`/`match_number` unique | PASS | 380 |
| 38 rounds x 10 fixtures | PASS | |
| players `player_id` unique | PASS | 404 |
| player names unique (no stable ID) | **WARN** | 4 rows share a name |
| player_season_stats `(player_id, season)` unique | PASS | 404, season=2025/26 |
| team_season_stats `(team_id, season)` unique | PASS | 160 |
| points == 3*wins+draws; mp == w+d+l; 38 games/team | PASS | 0 bad rows |
| match rates home/away (matches->teams) | PASS | 3040/3040 = 100% |
| match rates (fixtures->teams, players->teams, player-season->teams, team-season->teams) | PASS | 100% |

The single WARN is the documented limitation that players are keyed by name (no stable ID):
2 names are each shared by two players on different squads, so they are kept as distinct
`player_id`s rather than merged.

---

## 9. Entity-relationship summary

```text
teams_master (team_id) 1 -- N matches_master        (home_team_id / away_team_id)
teams_master (team_id) 1 -- N fixtures_2026_27      (home_team_id / away_team_id)
teams_master (team_id) 1 -- N team_season_stats     (team_id)
teams_master (team_id) 1 -- N players_master        (team_id)
teams_master (team_id) 1 -- N player_season_stats   (team_id)
players_master (player_id) 1 -- N player_season_stats (player_id)
matches_master (match_id) 1 -- 1 match_odds          (match_id)
```

Join keys for later work:
- Match features: `matches_master` joined to `team_season_stats` on `(home_team_id, season)`
  and `(away_team_id, season)`.
- Player features: `player_season_stats` joined to `players_master` on `player_id`, to
  `teams_master` on `team_id`.
- Fixture prediction: `fixtures_2026_27` joined to `teams_master` on `home_team_id` /
  `away_team_id`; team-season history via `team_id`.

---

## 10. Data-loss accounting

Nothing was silently dropped:
- Odds columns -> `match_odds.csv` (preserved, excluded from modelling tables by design).
- 1582 non-EPL player rows excluded from the PL layer, counted in section 2.
- `E0 (7).csv` was an MD5 duplicate of `E0 (8).csv`; only the surviving copy is used.
- All 39 team-name spellings are retained in `team_aliases.csv`.

## 11. Known limitations

- Player data covers one season (2025/26) only; no historical player-season stats.
- No stable player ID in the source; `player_id` is a per-season snapshot key
  (2 names are shared by different players -> kept separate).
- 2018/19 has no `kickoff_time` (raw file has no `Time` column).
- Historical E0 files carry no round number, so `matches_master` has no round column
  (only `fixtures_2026_27` has `round_number`).
- Teams promoted for 2026/27 (Coventry, Hull) have no historical match rows.
