from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.generer_catalogue import ErreurCatalogue, charger_diffusion
from scripts.promouvoir_diffusion import ErreurPromotion, promouvoir


ROOT = Path(__file__).parents[1]


class DiffusionTest(unittest.TestCase):
    def test_stable_release_contains_only_stable_packages(self) -> None:
        diffusion = charger_diffusion(ROOT / "config/releases/stable.json", "stable")
        self.assertEqual(
            set(diffusion.applications),
            {"arcenal", "arcenal_ats", "arcenal-store", "arcenal-systeme"},
        )

    def test_release_rejects_a_channel_mismatch(self) -> None:
        with self.assertRaises(ErreurCatalogue):
            charger_diffusion(ROOT / "config/releases/stable.json", "preview")

    def test_preview_can_be_promoted_to_stable(self) -> None:
        source = json.loads((ROOT / "config/releases/preview.json").read_text(encoding="utf-8"))
        target = json.loads((ROOT / "config/releases/stable.json").read_text(encoding="utf-8"))
        result = promouvoir(source, target)
        self.assertEqual(result["channel"], "stable")
        self.assertEqual(
            set(result["applications"]),
            {"arcenal", "arcenal_ats", "arcenal-store", "arcenal-systeme"},
        )
        self.assertEqual(result["applications"]["arcenal-systeme"], source["applications"]["arcenal-systeme"])
        self.assertEqual(result["applications"]["arcenal_ats"], source["applications"]["arcenal_ats"])
        self.assertEqual(result["promoted_from"], "preview")

    def test_development_cannot_skip_preview(self) -> None:
        source = json.loads((ROOT / "config/releases/development.json").read_text(encoding="utf-8"))
        target = json.loads((ROOT / "config/releases/stable.json").read_text(encoding="utf-8"))
        with self.assertRaises(ErreurPromotion):
            promouvoir(source, target)

    def test_selective_promotion_preserves_other_packages(self) -> None:
        source = json.loads((ROOT / "config/releases/development.json").read_text(encoding="utf-8"))
        target = json.loads((ROOT / "config/releases/preview.json").read_text(encoding="utf-8"))
        previous_ats = target["applications"]["arcenal_ats"]
        result = promouvoir(source, target, ("arcenal",))
        self.assertEqual(result["applications"]["arcenal"], source["applications"]["arcenal"])
        self.assertEqual(result["applications"]["arcenal_ats"], previous_ats)

    def test_selective_promotion_rejects_unknown_package(self) -> None:
        source = json.loads((ROOT / "config/releases/development.json").read_text(encoding="utf-8"))
        target = json.loads((ROOT / "config/releases/preview.json").read_text(encoding="utf-8"))
        with self.assertRaises(ErreurPromotion):
            promouvoir(source, target, ("application-inconnue",))

    def test_invalid_release_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "release.json"
            path.write_text('{"schema":"wrong"}', encoding="utf-8")
            with self.assertRaises(ErreurCatalogue):
                charger_diffusion(path, "stable")

    def test_release_rejects_a_duplicate_application_identifier(self) -> None:
        content = (
            '{"schema":"arcenal-release/v1","channel":"stable","applications":'
            '{"arcenal_ats":{"revision":"4ded5b7ab103945f10d2bce18baa2302aa983588","version":"0.1.0~ynh13"},'
            '"arcenal_ats":{"revision":"4b959c7aea6c0e7f3973a6332655eca34f532cea","version":"0.1.0~ynh10"}}}'
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "release.json"
            path.write_text(content, encoding="utf-8")
            with self.assertRaises(ErreurCatalogue):
                charger_diffusion(path, "stable")

    def test_release_rejects_a_short_git_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "release.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": "arcenal-release/v1",
                        "channel": "stable",
                        "applications": {
                            "arcenal-systeme": {"revision": "47b5c82", "version": "0.7.0~ynh1"}
                        },
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ErreurCatalogue):
                charger_diffusion(path, "stable")


if __name__ == "__main__":
    unittest.main()
