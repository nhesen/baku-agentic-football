"""Guard the exact workshop bundle that is copied into the five runtimes."""
import json
from pathlib import Path
import unittest

from baku_fc.config import load_settings


ROOT = Path(__file__).resolve().parents[1]
WORKSHOP = ROOT / "workshop" / "ai-team-baku-v6"


class WorkshopBundleTests(unittest.TestCase):
    def test_all_five_slots_use_the_canonical_runtime(self):
        for slot, pid in (("ai-gk", 0), ("ai-def", 1), ("ai-mid", 2),
                          ("ai-fwd1", 3), ("ai-fwd2", 4)):
            source = (WORKSHOP / slot / "src" / "main.py").read_text(encoding="utf-8")
            self.assertIn("from baku_fc.runtime import create_app", source)
            self.assertIn(f"app = create_app({pid})", source)

    def test_deploy_copies_canonical_package_and_workshop_settings(self):
        script = (WORKSHOP / "deploy-all.sh").read_text(encoding="utf-8")
        self.assertIn('cp -R "$REPO_ROOT/baku_fc" "$STAGE/src/baku_fc"', script)
        self.assertIn('cp "$SCRIPT_DIR/settings.workshop.json" "$STAGE/src/baku_fc/settings.json"', script)

    def test_gpt_56_luna_is_the_deployed_model(self):
        raw = json.loads((WORKSHOP / "settings.workshop.json").read_text(encoding="utf-8"))
        self.assertEqual(raw["model_id"], "us.openai.gpt-5.6-luna")
        self.assertEqual(load_settings(WORKSHOP / "settings.workshop.json").model_id,
                         "us.openai.gpt-5.6-luna")


if __name__ == "__main__":
    unittest.main()
