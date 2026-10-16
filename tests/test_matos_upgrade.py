import json
import unittest
from pathlib import Path

from scripts.generer_catalogue import applications_arcenal, charger_diffusion, charger_toml, serialiser_application_arc


ROOT = Path(__file__).parents[1]


class MatosUpgradeAvailability(unittest.TestCase):
    def test_qualified_preview_is_upgradable_not_flagged_broken(self):
        config = charger_toml(ROOT / "config/catalogue-client.toml")
        proof = json.loads((ROOT / "acceptance/MATOS_QUALIFICATION.json").read_text())
        for channel in ("development", "preview"):
            with self.subTest(channel=channel):
                release = charger_diffusion(ROOT / f"config/releases/{channel}.json", channel)
                app = next(item for item in applications_arcenal(config, release) if item.identifiant == "arcenal-matos")
                value = serialiser_application_arc(app)
                # app_upgrade_infos rejects state != working or level < 5.
                self.assertEqual(value["state"], "working")
                self.assertIsInstance(value["level"], int)
                self.assertGreaterEqual(value["level"], 5)
                self.assertEqual(value["level"], proof["arcenal_technical_level"])
                self.assertEqual(value["manifest"]["version"], proof["version"])
                self.assertNotEqual(value["manifest"]["version"], "0.1.1~ynh5")
                self.assertGreater(tuple(map(int, value["manifest"]["version"].split("~")[0].split("."))), (0, 1, 2))
                self.assertEqual(value["git"]["revision"], proof["revision"])
                published = json.loads((ROOT / f"{channel}/v3/apps.json").read_text())["apps"]["arcenal-matos"]
                self.assertEqual(published, value)
        self.assertIn("TEST_UPGRADE_FROM_PUBLISHED_VERSION", proof["successful_scenarios"])
        self.assertEqual(proof["upgrade_from"], "3d882348b212835d9adc61c54416ad72a6185c04")
        self.assertIn("EPI actif en SSO", proof["module_web_checks"])
        self.assertIn("Dosimètres inactif refusé 404", proof["module_web_checks"])
        stable = charger_diffusion(ROOT / "config/releases/stable.json", "stable")
        self.assertNotIn("arcenal-matos", stable.applications)

    def test_official_and_arcenal_qualifications_are_not_confused(self):
        proof = json.loads((ROOT / "acceptance/MATOS_QUALIFICATION.json").read_text())
        self.assertEqual(proof["official_yunohost_level"], 0)
        self.assertEqual(proof["arcenal_technical_level"], 5)
        self.assertEqual(proof["official_catalog_only_findings"], {
            "error": ["AppCatalog.state_is_working"], "critical": ["AppCatalog.is_in_catalog"]})
