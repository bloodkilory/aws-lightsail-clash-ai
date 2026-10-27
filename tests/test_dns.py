"""DNS regressions use synthetic identities; no live PF, TUN or AWS changes."""
import http.client
import json
import os
import plistlib
import re
import shutil
import socket
import subprocess
import tempfile
import time
import unittest
import urllib.parse
from pathlib import Path


class DnsTests(unittest.TestCase):
    def test_dns_stays_on_aws_when_selector_changes(self):
        dns = RENDERED['clash.yaml'].split('\ndns:\n')[1].split('\nproxies:')[0]
        for field in ('nameserver', 'default-nameserver', 'proxy-server-nameserver', 'direct-nameserver'):
            self.assertRegex(dns, r'  ' + field + r':\n  - https://1\.1\.1\.1/dns-query#AWS 新加坡\n  - https://8\.8\.8\.8/dns-query#AWS 新加坡&ecs=0\.0\.0\.0/0&ecs-override=true')
        self.assertNotIn('#DIRECT', dns)
        self.assertNotIn('#节点选择', dns)
        self.assertNotIn('fallback:', dns)

    def test_official_and_dns_routes_precede_domestic_rules(self):
        body = RENDERED['clash.yaml']
        limit = body.index('- GEOSITE,cn,DIRECT')
        for domain in ('anthropic.com', 'claude.ai', 'claude.com', 'claude.app',
                       'claudeusercontent.com', 'claudemcpcontent.com'):
            self.assertLess(body.index('- DOMAIN-SUFFIX,' + domain + ',AWS 新加坡'), limit)
        for rule in ('GEOSITE,category-doh,AWS 新加坡', 'GEOSITE,category-httpdns-cn,AWS 新加坡',
                     'DST-PORT,53,REJECT', 'DST-PORT,853,AWS 新加坡'):
            self.assertLess(body.index('- ' + rule), limit)
        self.assertIn('- any:53', body)
        self.assertIn('- tcp://any:53', body)

    def test_guard_blocks_physical_interfaces_only(self):
        with tempfile.TemporaryDirectory() as folder:
            script = Path(folder) / 'guard.sh'
            script.write_text(RENDERED['macos-dns-guard.sh'])
            result = subprocess.run(['/bin/sh', str(script), '--print-rules', 'lo0', 'utun7',
                                     'en0', 'bridge2', 'en6', 'awdl0', 'en1;bad'],
                                    capture_output=True, text=True, check=True)
            rule = result.stdout
            self.assertIn('on { en0, bridge2, en6 }', rule)
            self.assertIn('proto { tcp udp }', rule)
            self.assertIn('port { 53, 853 }', rule)
            for forbidden in ('utun', 'lo0', 'awdl', '! lo0', 'bad'):
                self.assertNotIn(forbidden, rule)
            empty = subprocess.run(['/bin/sh', str(script), '--print-rules', 'lo0', 'utun7'],
                                   capture_output=True, text=True)
            self.assertNotEqual(empty.returncode, 0)
            self.assertEqual(empty.stdout, '')

    def test_shell_templates_and_startup_job(self):
        for body in re.findall(r'```(?:bash|sh)\n(.*?)\n```', TEXT, re.S):
            result = subprocess.run(['/bin/bash', '-n'], input=body, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        job = plistlib.loads(RENDERED['local.clash-dns-guard.plist'].encode())
        self.assertTrue(job['RunAtLoad'])
        self.assertEqual(job['ProgramArguments'], ['/usr/local/libexec/clash-dns-guard'])

    def test_watchdog_rolls_back_only_its_own_guard(self):
        self.check_watchdog(committed=False)

    def test_committed_install_is_not_rolled_back(self):
        self.check_watchdog(committed=True)

    def check_watchdog(self, committed):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            trial = root / 'trial'
            trial.mkdir()
            commands = root / 'commands'
            commands.mkdir()
            calls = root / 'calls'
            calls.touch()
            # Substitute only external command/path boundaries; never invoke real PF or launchd.
            for name, body in {'id': 'echo 0', 'sleep': ':',
                               'pfctl': 'printf "pfctl %s\\n" "$*" >> "$CALL_LOG"',
                               'launchctl': 'printf "launchctl %s\\n" "$*" >> "$CALL_LOG"'}.items():
                executable = commands / name
                executable.write_text('#!/bin/sh\n' + body + '\n')
                executable.chmod(0o700)
            script = RENDERED['macos-dns-rollback.sh']
            script = script.replace('PATH=/usr/bin:/bin:/usr/sbin:/sbin',
                                    'PATH=' + str(commands) + ':/usr/bin:/bin')
            script = script.replace('/var/run/local.clash-dns-guard.trial', str(trial))
            paths = []
            for index, path in enumerate(('/var/run/local.clash-dns-guard.token',
                                          '/usr/local/libexec/clash-dns-guard',
                                          '/Library/LaunchDaemons/local.clash-dns-guard.plist',
                                          '/etc/pf.anchors/local.clash-dns-guard')):
                target = root / str(index)
                target.write_text('12345\n')
                paths.append(target)
                script = script.replace(path, str(target))
            if committed:
                (trial / 'decision').mkdir()
                (trial / 'result').write_text('COMMITTED\n')
            rollback = root / 'rollback.sh'
            rollback.write_text(script)
            subprocess.run(['/bin/sh', str(rollback), '--watch'], check=True,
                           env={**os.environ, 'CALL_LOG': str(calls)}, capture_output=True)
            if committed:
                self.assertEqual(calls.read_text(), '')
                self.assertTrue(all(p.exists() for p in paths))
                self.assertEqual((trial / 'result').read_text(), 'COMMITTED\n')
            else:
                self.assertEqual(calls.read_text().splitlines(), [
                    'launchctl bootout system/local.clash-dns-guard',
                    'pfctl -a com.apple/000.clash-dns-guard -f /dev/null',
                    'pfctl -X 12345'])
                self.assertTrue(all(not p.exists() for p in paths))
                self.assertEqual((trial / 'result').read_text(), 'ROLLED_BACK\n')

    @unittest.skipUnless(os.environ.get('MIHOMO_BIN'), 'MIHOMO_BIN not set')
    def test_unavailable_aws_does_not_fall_back_to_direct_dns(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            control = str(root / 'control.sock')
            body = RENDERED['clash.yaml'].replace('mixed-port: 7897', 'mixed-port: 0')
            body = body.replace('server: "8.8.8.8"', 'server: "127.0.0.1"').replace('  port: 443', '  port: 9')
            # No live listener or TUN; the proxy can only connect to a closed loopback port.
            body += '\nexternal-controller-unix: ' + json.dumps(control) + '\n'
            body = body.replace('store-selected: true', 'store-selected: false')
            (root / 'config.yaml').write_text(body)
            for name in ('geosite.dat', 'geoip.dat', 'Country.mmdb'):
                source = Path(os.environ['MIHOMO_DATA_DIR']) / name
                if source.exists():
                    shutil.copyfile(source, root / name)

            def api(method, path, value=None):
                sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                sock.settimeout(20)
                try:
                    sock.connect(control)
                except OSError:
                    sock.close()
                    raise
                client = http.client.HTTPConnection('localhost', timeout=20)
                client.sock = sock
                try:
                    client.request(method, path, body=json.dumps(value) if value else None,
                                   headers={'Content-Type': 'application/json'})
                    response = client.getresponse()
                    data = response.read()
                    return response.status, json.loads(data) if data else {}
                finally:
                    client.close()

            with (root / 'core.log').open('w+') as log:
                process = subprocess.Popen([os.environ['MIHOMO_BIN'], '-d', folder, '-f', str(root / 'config.yaml')],
                                           stdout=log, stderr=log)
                try:
                    for _ in range(100):
                        try:
                            if '节点选择' in api('GET', '/proxies')[1].get('proxies', {}):
                                break
                        except (OSError, http.client.HTTPException):
                            pass
                        if process.poll() is not None:
                            log.seek(0)
                            self.fail(log.read())
                        time.sleep(.05)
                    else:
                        self.fail('Isolated core readiness timeout')
                    path = '/proxies/' + urllib.parse.quote('节点选择', safe='')
                    self.assertEqual(api('PUT', path, {'name': 'DIRECT'})[0], 204)
                    status, result = api('GET', '/dns/query?name=www.baidu.com&type=A')
                    self.assertFalse([x for x in result.get('Answer', []) if x.get('type') in (1, 28)])
                    self.assertTrue(status >= 400 or result.get('Status') == 2, result)
                finally:
                    process.terminate()
                    process.wait(timeout=5)
