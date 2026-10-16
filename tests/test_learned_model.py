import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from baku_fc.config import Settings
from baku_fc.learned import model, retention
from baku_fc.version import policy_fingerprint


class LearnedModelChecks(unittest.TestCase):
    def test_real_artifact_has_held_out_seed_validation(self):
        m=model()
        self.assertGreater(m["training_samples"],1000)
        self.assertFalse(set(m["validation_seeds"]) & set(m["validation_model_trained_on"]))
        self.assertLess(m["validation_metrics"]["log_loss"],m["constant_validation_metrics"]["log_loss"])
        self.assertTrue(0 < retention([.2,.1,.4,.7,.3,0,.2]) < 1)
    def test_active_model_is_part_of_policy_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);(p/"version.py").write_text("# frozen code")
            path=p/"pass_model.json";path.write_text("first")
            with patch("baku_fc.version.__file__",str(p/"version.py")):
                enabled=Settings(use_pass_model=True);disabled=Settings(use_pass_model=False)
                a,b=policy_fingerprint(enabled),policy_fingerprint(disabled)
                path.write_text("changed weights")
                self.assertNotEqual(a,policy_fingerprint(enabled))
                self.assertEqual(b,policy_fingerprint(disabled))


if __name__=="__main__":unittest.main()
