import unittest
from pathlib import Path

from scripts.generer_catalogue import applications_arcenal, charger_diffusion, charger_toml, serialiser_application_arc

ROOT = Path(__file__).resolve().parents[1]


class OscarPreviewTest(unittest.TestCase):
    def test_preview_is_pinned_without_changing_stable(self):
        config = charger_toml(ROOT / "config/catalogue-client.toml")
        expected = "ac3c74ab2bdb8d8904062e7a268e8d08e33a9067"
        for channel in ("development", "preview"):
            release = charger_diffusion(ROOT / f"config/releases/{channel}.json", channel)
            app = next(item for item in applications_arcenal(config, release) if item.identifiant == "oscar")
            value = serialiser_application_arc(app)
            self.assertEqual(value["git"], {"url": "https://github.com/arcenal-coder/oscar_ynh", "branch": "preview", "revision": expected})
            self.assertEqual(value["manifest"]["version"], "1.0.0~ynh1")
            self.assertEqual(value["level"], 0)
            self.assertFalse(value["manifest"]["integration"]["sso"])
            self.assertTrue(value["manifest"]["integration"]["multi_instance"])
        stable = charger_diffusion(ROOT / "config/releases/stable.json", "stable")
        self.assertNotIn("oscar", stable.applications)
        self.assertNotIn("oscar", {item.identifiant for item in applications_arcenal(config, stable) if "stable" in item.canaux})
