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
        self.assertEqual(set(diffusion.applications), {"arcenal-store", "arcenal-systeme"})

    def test_release_rejects_a_channel_mismatch(self) -> None:
        with self.assertRaises(ErreurCatalogue):
            charger_diffusion(ROOT / "config/releases/stable.json", "preview")

    def test_preview_can_be_promoted_to_stable(self) -> None:
        source = json.loads((ROOT / "config/releases/preview.json").read_text(encoding="utf-8"))
        target = json.loads((ROOT / "config/releases/stable.json").read_text(encoding="utf-8"))
        result = promouvoir(source, target)
        self.assertEqual(result["channel"], "stable")
        self.assertEqual(set(result["applications"]), {"arcenal-store", "arcenal-systeme"})
        self.assertEqual(result["applications"]["arcenal-systeme"], source["applications"]["arcenal-systeme"])
        self.assertEqual(result["promoted_from"], "preview")

    def test_development_cannot_skip_preview(self) -> None:
        source = json.loads((ROOT / "config/releases/development.json").read_text(encoding="utf-8"))
        target = json.loads((ROOT / "config/releases/stable.json").read_text(encoding="utf-8"))
        with self.assertRaises(ErreurPromotion):
            promouvoir(source, target)

    def test_invalid_release_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "release.json"
            path.write_text('{"schema":"wrong"}', encoding="utf-8")
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
