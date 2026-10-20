"""YunoHost 12.1 _app_upgrade_infos: working + integer level >= 5."""
import json
import tomllib
import unittest
import tempfile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from generer_catalogue import charger_diffusion, applications_arcenal, ErreurCatalogue, construire_catalogue
from promouvoir_diffusion import promouvoir


def upgrade_quality_allowed(entry):
    return isinstance(entry.get("level"), int) and entry["level"] >= 5 and entry.get("state") == "working"


class VigilanceUpgradeTest(unittest.TestCase):
    def test_quality_is_attached_to_the_qualified_revision_only(self):
        declaration=tomllib.loads((ROOT/'config/catalogue-client.toml').read_text())
        source=json.loads((ROOT/'config/releases/development.json').read_text())
        target=json.loads((ROOT/'config/releases/preview.json').read_text())
        source['applications']['arcenalportail']['level']=5
        target['applications']['arcenalportail']['level']=0
        with tempfile.TemporaryDirectory() as folder:
            a=Path(folder)/'dev.json';b=Path(folder)/'preview.json'
            a.write_text(json.dumps(source));b.write_text(json.dumps(target))
            dev=charger_diffusion(a,'development');preview=charger_diffusion(b,'preview')
            get=lambda release:next(app for app in applications_arcenal(declaration,release) if app.identifiant=='arcenalportail')
            self.assertEqual(get(dev).niveau,5)
            self.assertEqual(get(preview).niveau,0)
        promoted=promouvoir(source,target,['arcenalportail'])
        self.assertEqual(promoted['applications']['arcenalportail']['level'],5)

    def test_invalid_revision_quality_is_rejected(self):
        source=json.loads((ROOT/'config/releases/development.json').read_text())
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'release.json'
            for level in [True,-1,9,'5',None]:
                source['applications']['arcenalportail']['level']=level
                path.write_text(json.dumps(source))
                with self.assertRaises(ErreurCatalogue):charger_diffusion(path,'development')

    def test_unqualified_zero_blocks_yunohost_updates(self):
        self.assertFalse(upgrade_quality_allowed({"state": "working", "level": 0}))
        self.assertFalse(upgrade_quality_allowed({"state": "notworking", "level": 5}))
        self.assertTrue(upgrade_quality_allowed({"state": "working", "level": 5}))

    def test_development_candidate_has_real_qualification_and_upgrade_quality(self):
        entry = json.loads((ROOT/"development/v3/apps.json").read_text())["apps"]["arcenalportail"]
        self.assertTrue(upgrade_quality_allowed(entry), "Le niveau publié désactive la mise à jour YunoHost.")
        proof = json.loads((ROOT/"acceptance/vigilance-native.json").read_text())
        self.assertTrue(all(proof["private_catalog_criteria"].values()))
        self.assertIs(proof.get('native_mail_verified'),True)
        self.assertIn('6af4b824abab2f52862406d4fa5c2155b439386a',proof['upgrade_from'])
        self.assertGreaterEqual(len(proof['evidence'][0]['tests']),12)
        self.assertEqual(entry["level"], proof["arcenal_technical_level"])
        self.assertEqual(entry["git"]["revision"], proof["qualified_commit"])
        self.assertEqual(entry["manifest"]["version"], proof["evidence"][0]["app_version"])
        self.assertEqual(entry["git"]["branch"], "preview")
        config = tomllib.loads((ROOT/"config/catalogue-client.toml").read_text())
        declaration = next(app for app in config["applications"]["arcenal"] if app["id"] == "arcenalportail")
        self.assertIn("arcenalportail_ynh/actions/runs/", declaration["preuve_qualification"])

    def test_official_selective_promotion_makes_preview_upgradeable(self):
        source=json.loads((ROOT/'config/releases/development.json').read_text())
        target=json.loads((ROOT/'config/releases/preview.json').read_text())
        promoted=promouvoir(source,target,['arcenalportail'])
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'promoted.json';path.write_text(json.dumps(promoted))
            release=charger_diffusion(path,'preview')
            config=tomllib.loads((ROOT/'config/catalogue-client.toml').read_text())
            base=json.loads((ROOT/'preview/v3/apps.json').read_text())
            entry=construire_catalogue(base,config,'preview',release)['apps']['arcenalportail']
        self.assertTrue(upgrade_quality_allowed(entry))
        proof=json.loads((ROOT/'acceptance/vigilance-native.json').read_text())
        self.assertEqual(entry['git']['revision'],proof['qualified_commit'])


if __name__ == "__main__": unittest.main()
