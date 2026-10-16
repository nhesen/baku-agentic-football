"""Offline decision/benchmark tools. Never make a Bedrock request."""
from __future__ import annotations

import argparse
import json
import statistics
import time
from dataclasses import replace
from pathlib import Path

from .config import load_settings
from .engine import Engine


def main():
    ap = argparse.ArgumentParser(description="Baku FC offline probe; no AWS calls")
    ap.add_argument("payload", help="JSON payload file")
    ap.add_argument("--player", type=int, default=0)
    ap.add_argument("--all", action="store_true", help="evaluate all five player runtimes")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--output", help="save diagnostic JSON")
    args = ap.parse_args()
    if not 1 <= args.repeat <= 10000:
        ap.error("repeat must be 1..10000")
    data = json.loads(Path(args.payload).read_text(encoding="utf-8-sig"))
    cfg = replace(load_settings(), use_llm=False)
    results, times = [], []
    for pid in range(5) if args.all else [args.player]:
        engine = Engine(pid, cfg)
        for _ in range(args.repeat):
            # For --all, mimic the portal's one-player request per runtime.
            raw = json.loads(json.dumps(data))
            if args.all:
                inner = raw.get("prompt", raw)
                was_text = isinstance(inner, str)
                inner = json.loads(inner) if was_text else inner
                inner["myPlayers"] = [pid]
                if "prompt" in raw:
                    raw["prompt"] = json.dumps(inner) if was_text else inner
            start = time.perf_counter()
            result = engine.decide(raw)
            times.append((time.perf_counter() - start) * 1000)
        results.append(result)
        engine.close()
    report = {"mode": "offline_fallback_only", "results": results,
              "timing": {"samples": len(times), "p50_ms": round(statistics.median(times), 3),
                         "p95_ms": round(sorted(times)[max(0, int(len(times) * 0.95) - 1)], 3)},
              "limitation": "Local Python timing only; not model/network latency or match win rate."}
    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
