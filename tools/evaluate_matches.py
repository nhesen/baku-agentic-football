"""Summarize actual match CSVs; never manufacture match results or win rates."""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


def evaluate(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    groups, conditions, seen = defaultdict(list), defaultdict(Counter), set()
    for i, row in enumerate(rows, 2):
        if not any(str(v or "").strip() for v in row.values()):
            continue
        for field in ("version", "opponent", "side", "goals_for", "goals_against", "match_id"):
            if not row.get(field, "").strip():
                raise ValueError(f"Line {i}: missing {field}")
        if row["side"] not in {"home", "away"}:
            raise ValueError(f"Line {i}: side must be home or away")
        if row["match_id"] in seen:
            raise ValueError(f"Line {i}: duplicate match_id")
        seen.add(row["match_id"])
        try:
            gf, ga = int(row["goals_for"]), int(row["goals_against"])
        except ValueError as exc:
            raise ValueError(f"Line {i}: goals must be integers") from exc
        if gf < 0 or ga < 0:
            raise ValueError(f"Line {i}: goals cannot be negative")
        groups[row["version"]].append((gf, ga))
        conditions[row["version"]][(row["opponent"], row["side"])] += 1
    summaries = []
    for version, games in groups.items():
        wins = sum(a > b for a, b in games)
        draws = sum(a == b for a, b in games)
        summaries.append({"version": version, "matches": len(games), "wins": wins,
                          "draws": draws, "losses": len(games) - wins - draws,
                          "points": wins * 3 + draws, "goal_difference": sum(a-b for a, b in games)})
    summaries.sort(key=lambda r: (-r["points"] / r["matches"], -r["goal_difference"] / r["matches"]))
    sets = list(conditions.values())
    paired = bool(len(sets) > 1 and all(s == sets[0] for s in sets))
    return {"versions": summaries, "same_opponent_side_coverage": paired,
            "note": "No matches recorded." if not summaries else
            "Descriptive results only. Match counts, opponents, sides and repetitions must be comparable; small samples do not prove superiority."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("csv")
    args = p.parse_args()
    try:
        print(json.dumps(evaluate(args.csv), indent=2))
    except (OSError, ValueError) as exc:
        p.error(str(exc))


if __name__ == "__main__":
    main()
