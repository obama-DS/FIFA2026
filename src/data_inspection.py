# Data Inventory Inspector
# Reads every CSV in the data directory (recursively) and prints a report.
# Read-only: original datasets are never modified.

import argparse
import hashlib
import os

import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)
pd.set_option("display.max_colwidth", 40)


# ---------- File helpers ----------

def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def read_csv(path):
    for sep in (",", "\t"):
        for encoding in ("utf-8-sig", "latin-1"):
            try:
                df = pd.read_csv(path, sep=sep, encoding=encoding)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
    return pd.read_csv(path, sep=r"\s+", engine="python")


# ---------- Key detection ----------

def single_col_keys(df):
    keys = []
    for col in df.columns:
        if df[col].notna().all() and df[col].nunique(dropna=True) == len(df):
            keys.append(col)
    return keys


def composite_keys(df):
    found = []
    candidates = [
        ["Date", "HomeTeam", "AwayTeam"],
        ["Date", "Home Team", "Away Team"],
        ["Round Number", "Home Team", "Away Team"],
        ["Player", "Squad", "Comp"],
    ]
    for cand in candidates:
        if all(c in df.columns for c in cand):
            n_unique = df[cand].drop_duplicates().shape[0]
            if n_unique == len(df):
                found.append(cand)
    return found


# ---------- Season / identifier helpers ----------

def infer_season(df):
    if "Date" not in df.columns:
        return None
    dates = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")
    if dates.notna().sum() == 0:
        return None
    start, end = dates.min().year, dates.max().year
    label = f"{start}/{str(end)[2:]}" if end > start else str(start)
    return f"{label}  ({dates.min():%d/%m/%Y} to {dates.max():%d/%m/%Y})"


def identifier_columns(df):
    keywords = {
        "player": ["player", "nation", "born", "age", "pos"],
        "team": ["team", "squad", "club"],
        "match": ["date", "match", "round", "referee", "div", "location", "stadium", "time"],
        "result": ["fthg", "ftag", "ftr", "hthg", "htag", "htr", "result"],
    }
    found = {}
    for label, words in keywords.items():
        hits = [c for c in df.columns if any(w in c.lower() for w in words)]
        if hits:
            found[label] = hits
    return found


def season_columns(df):
    return [c for c in df.columns if "season" in c.lower()]


# ---------- Per-table report ----------

def inspect_table(path):
    name = os.path.basename(path)
    print("\n" + "#" * 70)
    print(f"FILE: {name}")
    print("#" * 70)

    try:
        df = read_csv(path)
    except Exception as e:
        print(f"Could not read file: {e}")
        return None

    print(f"\n[1] Shape: {df.shape[0]} rows x {df.shape[1]} columns")
    print(f"    File size: {os.path.getsize(path):,} bytes  |  MD5: {md5(path)}")

    print("\n[2] Column names:")
    print(df.columns.tolist())

    print("\n[3] Data types:")
    print(df.dtypes.to_string())

    print("\n[4] First 3 rows:")
    print(df.head(3).to_string())

    print("\n[5] Missing-value counts (columns with any):")
    missing = df.isna().sum()
    missing = missing[missing > 0]
    if missing.empty:
        print("    No missing values.")
    else:
        print(missing.to_string())

    print("\n[6] Duplicate rows: ", int(df.duplicated().sum()))

    print("\n[7] Likely primary keys:")
    single = single_col_keys(df)
    comp = composite_keys(df)
    if single:
        print("    Single-column candidates:", single)
    else:
        print("    Single-column candidates: none (no fully unique column)")
    if comp:
        for c in comp:
            print("    Composite candidate:", c)
    else:
        print("    Composite candidates: none detected")

    print("\n[8] Season columns:", season_columns(df) or "none in the data")
    print("    Inferred season (from Date):", infer_season(df))

    print("\n[9] Player/team/match identifiers:")
    ident = identifier_columns(df)
    if not ident:
        print("    none detected")
    for label, cols in ident.items():
        print(f"    {label}: {cols}")

    return df


# ---------- Cross-dataset relationships ----------

def team_universe(df):
    if "HomeTeam" in df.columns and "AwayTeam" in df.columns:
        return set(df["HomeTeam"]).union(set(df["AwayTeam"]))
    if "Home Team" in df.columns and "Away Team" in df.columns:
        return set(df["Home Team"]).union(set(df["Away Team"]))
    if "Squad" in df.columns:
        return set(df["Squad"])
    return None


def detect_relationships(tables):
    print("\n" + "#" * 70)
    print("RELATIONSHIPS BETWEEN DATASETS")
    print("#" * 70)

    for i in range(len(tables)):
        for j in range(i + 1, len(tables)):
            name_i, df_i = tables[i]
            name_j, df_j = tables[j]
            shared = sorted(set(df_i.columns) & set(df_j.columns))
            line = f"{name_i}  <->  {name_j}"
            if shared:
                print(f"\n{line}  | shared columns ({len(shared)}): {shared[:20]}{' ...' if len(shared) > 20 else ''}")
            teams_i = team_universe(df_i)
            teams_j = team_universe(df_j)
            if teams_i and teams_j:
                common = sorted(teams_i & teams_j)
                print(f"    team/player entity overlap: {len(common)} shared values")
                missing = sorted(teams_j - teams_i)
                if missing:
                    print(f"    values in {name_j} not in {name_i}: {missing[:15]}{' ...' if len(missing) > 15 else ''}")
            elif shared:
                print(f"    entity overlap: none")


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(description="Inspect all CSV files in a directory.")
    parser.add_argument("--data-dir", default=os.path.join(os.path.dirname(__file__), ".."),
                        help="Directory containing the CSV datasets (default: project root)")
    args = parser.parse_args()
    data_dir = os.path.abspath(args.data_dir)

    csv_files = []
    for root, dirs, files in os.walk(data_dir):
        for f in sorted(files):
            if f.lower().endswith(".csv"):
                csv_files.append(os.path.join(root, f))

    print(f"Scanning {data_dir}")
    print(f"Found {len(csv_files)} CSV file(s)")

    hashes = {}
    for path in csv_files:
        hashes.setdefault(md5(path), []).append(os.path.basename(path))
    for h, names in hashes.items():
        if len(names) > 1:
            print(f"\nWARNING: identical file contents (MD5 {h}):")
            for n in names:
                print(f"    {n}")

    tables = []
    for path in csv_files:
        df = inspect_table(path)
        if df is not None:
            tables.append((os.path.basename(path), df))

    detect_relationships(tables)


if __name__ == "__main__":
    main()
