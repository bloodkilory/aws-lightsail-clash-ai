#!/usr/bin/env python3
"""Validate README templates locally; never call AWS or modify a live service."""
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path

README = Path(__file__).resolve().parents[1] / 'README.md'
TEXT = README.read_text()
BLOCKS = dict(re.findall(r'<!-- file: ([\w.-]+) -->\n```[^\n]*\n(.*?)\n```', TEXT, re.S))
renderer = types.ModuleType('renderer')
exec(compile(BLOCKS['render.py'], 'README:render.py', 'exec'), renderer.__dict__)
PARAMS = {'SERVER_IPV4': '8.8.8.8', 'REGION': 'ap-southeast-1',
          'INSTANCE_NAME': 'personal-proxy-sg', 'SNI': 'www.amazon.com',
          'QUOTA_BYTES': 2 * 1024 ** 4}
IDENTITY = {'UUID': '11111111-1111-4111-8111-111111111111',
            'PRIVATE_KEY': base64.urlsafe_b64encode(bytes(range(32))).decode().rstrip('='),
            'PUBLIC_KEY': base64.urlsafe_b64encode(bytes(range(32, 64))).decode().rstrip('='),
            'SHORT_ID': '1122334455667788', 'SUB_TOKEN': 'synthetic-test-token'}
RENDERED = {name: renderer.render(body, {**PARAMS, **IDENTITY})
            for name, body in BLOCKS.items() if name != 'render.py'}


class GuideTests(unittest.TestCase):
    def test_placeholders_and_policy(self):
        for name, body in RENDERED.items():
            self.assertNotRegex(body, r'@@[A-Z0-9_]+@@', name)
            if name.endswith('.json'):
                json.loads(body)
        policy = json.loads(RENDERED['iam-policy.json'])['Statement'][0]
        self.assertEqual(policy['Action'], 'lightsail:GetInstanceMetricData')
        self.assertEqual(policy['Condition']['IpAddress']['aws:SourceIp'], '8.8.8.8/32')

    def test_rerender_preserves_identity_and_private_file_modes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'README.md').write_text(TEXT)
            (root / 'render.py').write_text(BLOCKS['render.py'])
            (root / 'params.json').write_text(json.dumps(PARAMS))
            (root / 'identity.json').write_text(json.dumps(IDENTITY))
            for _ in range(2):
                subprocess.run([sys.executable, str(root / 'render.py')], check=True, capture_output=True)
                self.assertEqual(json.loads((root / 'identity.json').read_text()), IDENTITY)
                for path in (root / 'bundle').iterdir():
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                self.assertIn('8.8.8.8:8443/synthetic-test-token', (root / 'bundle/subscription-url.txt').read_text())

    def test_rule_and_dns_order(self):
        body = RENDERED['clash.yaml']
        self.assertLess(body.index('- DOMAIN,services.googleapis.cn'), body.index('- GEOSITE,cn,DIRECT'))
        self.assertLess(body.index('- GEOSITE,geolocation-!cn'), body.index('- GEOSITE,cn,DIRECT'))
        self.assertIn('IP-CIDR,8.8.8.8/32,DIRECT,no-resolve', body)

    @unittest.skipUnless(os.environ.get('MIHOMO_BIN'), 'MIHOMO_BIN not set')
    def test_actual_mihomo_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'config.yaml').write_text(RENDERED['clash.yaml'])
            data = Path(os.environ['MIHOMO_DATA_DIR'])
            for name in ('geosite.dat', 'geoip.dat', 'Country.mmdb'):
                if (data / name).exists():
                    shutil.copyfile(data / name, root / name)
            result = subprocess.run([os.environ['MIHOMO_BIN'], '-t', '-d', str(root), '-f', str(root / 'config.yaml')],
                                    capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


def load_tests(loader, tests, pattern):
    # Load the separately readable meter regression suite against the rendered code.
    temp = tempfile.TemporaryDirectory()
    root = Path(temp.name)
    (root / 'meter.py').write_text(RENDERED['meter.py'])
    source = (Path(__file__).with_name('test_meter.py')).read_text()
    module = types.ModuleType('generated_meter_tests')
    module.__file__ = str(root / 'test_meter.py')
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
    tests.addTests(loader.loadTestsFromTestCase(module.MeterTests))
    # Keep the temporary module alive until the complete test process exits.
    module.MeterTests.template_dir = temp
    import test_dns
    test_dns.RENDERED = RENDERED
    test_dns.TEXT = TEXT
    tests.addTests(loader.loadTestsFromTestCase(test_dns.DnsTests))
    if os.environ.get('CADDY_BIN'):
        import test_http
        test_http.RENDERED = RENDERED
        tests.addTests(loader.loadTestsFromTestCase(test_http.SubscriptionHttpTests))
    return tests


if __name__ == '__main__':
    unittest.main(verbosity=2)
