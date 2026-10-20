"""Pin the Report API/MCP candidate without promoting unrelated apps."""
import json
import unittest
from pathlib import Path

from scripts.generer_catalogue import applications_arcenal, charger_diffusion, charger_toml, serialiser_application_arc
from scripts.promouvoir_diffusion import promouvoir


ROOT = Path(__file__).parents[1]


class ReportUpgradeTest(unittest.TestCase):
    def test_report_candidate_has_exact_source_and_package_compatibility(self):
        config = charger_toml(ROOT / 'config/catalogue-client.toml')
        release = charger_diffusion(ROOT / 'config/releases/development.json', 'development')
        report = next(app for app in applications_arcenal(config, release) if app.identifiant == 'arcenal_report')
        value = serialiser_application_arc(report)
        self.assertEqual(value['manifest']['version'], '0.3.0~ynh1')
        self.assertEqual(value['git']['revision'], '1535cd9866b6753a9bf335698b9c399b5ff1e5cb')
        self.assertEqual(value['git']['branch'], 'preview')
        self.assertEqual(value['manifest']['integration']['yunohost'], '>= 12.1.17')
        self.assertEqual(value['manifest']['integration']['architectures'], ['amd64', 'arm64'])
        self.assertNotIn('stable', report.canaux)

    def test_selective_report_promotion_keeps_other_versions(self):
        source = json.loads((ROOT / 'config/releases/development.json').read_text())
        target = json.loads((ROOT / 'config/releases/preview.json').read_text())
        result = promouvoir(source, target, ('arcenal_report',))
        self.assertEqual(result['applications']['arcenal_report'], source['applications']['arcenal_report'])
        for name in target['applications']:
            if name != 'arcenal_report':
                self.assertEqual(result['applications'][name], target['applications'][name])


if __name__ == '__main__':
    unittest.main()
