"""Local build and actual-result evaluation contracts."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from tools.build_agents import build
from tools.evaluate_matches import evaluate

ROOT = Path(__file__).resolve().parents[1]


class ToolContracts(unittest.TestCase):
    def test_builder_has_five_self_contained_runtimes_and_no_otel_dependency(self):
        with tempfile.TemporaryDirectory(prefix="baku-build-") as tmp:
            out = build(ROOT, Path(tmp), None, "us-east-1")
            spec = json.loads((out / "agentcore" / "agentcore.json").read_text())
            self.assertEqual(len(spec["runtimes"]), 5)
            self.assertEqual(json.loads((out / "agentcore" / "aws-targets.json").read_text()), [])
            for pid, runtime in enumerate(spec["runtimes"]):
                src = out / runtime["codeLocation"]
                self.assertIn(f"create_app({pid})", (src / "main.py").read_text())
                self.assertTrue((src / "baku_fc" / "runtime.py").is_file())
                self.assertFalse(runtime["instrumentation"]["enableOtel"])
                self.assertIn("strands-agents==1.61.1", (src / "requirements.txt").read_text())

    def test_no_matches_means_no_fabricated_rank(self):
        report = evaluate(ROOT / "evaluation" / "matches.csv")
        self.assertEqual(report["versions"], [])

    def test_unequal_repetitions_are_not_equal_coverage(self):
        with tempfile.TemporaryDirectory(prefix="baku-results-") as tmp:
            file = Path(tmp) / "matches.csv"
            with file.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["version", "opponent", "side", "goals_for", "goals_against", "match_id"])
                writer.writerows([["a", "same", "home", 1, 0, "1"],
                                  ["a", "same", "home", 1, 0, "2"],
                                  ["b", "same", "home", 0, 1, "3"]])
            report = evaluate(file)
            self.assertFalse(report["same_opponent_side_coverage"])


if __name__ == "__main__":
    unittest.main()
