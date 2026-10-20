"""Prepare only VIGIlance development from an actual immutable native report."""
import argparse
import json
import re
from pathlib import Path

def require(condition, message):
    if not condition:
        raise ValueError(message)

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--proof',type=Path,required=True)
parser.add_argument('--run-url',required=True)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
proof=json.loads(args.proof.read_text())
require(proof['schema']=='arcenal-technical-qualification/v1', 'Unknown qualification schema')
require(set(proof['private_catalog_criteria'])=={'1','2','3','4','5'}, 'Missing native criteria')
require(all(value is True for value in proof['private_catalog_criteria'].values()), 'Failed native criteria')
require(type(proof['arcenal_technical_level']) is int and proof['arcenal_technical_level']==5, 'Expected proven level 5')
require(re.fullmatch('[0-9a-f]{40}',proof['qualified_commit']), 'Invalid qualified commit')
require(re.fullmatch('https://github.com/arcenal-coder/arcenalportail_ynh/actions/runs/[0-9]+',args.run_url), 'Invalid evidence URL')
report=proof['evidence'][0]
require(report['app']=='arcenalportail' and report['commit']==proof['qualified_commit'], 'Evidence does not match candidate')
require(report['tests'] and all(test['main_result']=='success' for test in report['tests']), 'Native tests failed or absent')
require(proof.get('native_mail_verified') is True, 'Real local-mail evidence required for workflow emails')
require('6af4b824abab2f52862406d4fa5c2155b439386a' in proof['upgrade_from'], 'Missing upgrade from published beta4 ynh2')
version=report['app_version']
require(re.fullmatch(r'[0-9a-z]+(?:[.+-][0-9a-z]+)*~ynh[0-9]+',version), 'Invalid YunoHost version')
release=json.loads((root/'config/releases/development.json').read_text())
release['applications']['arcenalportail']={'revision':proof['qualified_commit'],'version':version,'branch':'preview','level':5}
serialized=json.dumps(release,indent=2,ensure_ascii=False)+'\n'
for relative in ['config/releases/development.json','development/v1/release.json']:
    (root/relative).write_text(serialized)
(root/'acceptance/vigilance-native.json').write_text(json.dumps(proof,indent=2,ensure_ascii=False)+'\n')
config=root/'config/catalogue-client.toml'
text=config.read_text()
start=text.index('id = "arcenalportail"')
end=text.find('[[applications.arcenal]]',start)
if end<0:end=len(text)
block=text[start:end]
block=re.sub(r'^version = ".*"$',f'version = "{version}"',block,flags=re.M)
block=re.sub(r'^preuve_qualification = ".*"$',f'preuve_qualification = "{args.run_url}"',block,flags=re.M)
# Direct LDAP synchronization is not implemented; YunoHost SSO remains enabled.
block=re.sub(r'^ldap = true$', 'ldap = false',block,flags=re.M)
config.write_text(text[:start]+block+text[end:])
print('VIGIlance development reference prepared from native proof; preview awaits the official promotion.')
