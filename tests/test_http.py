"""Exercise a local Caddy binary against synthetic subscription data."""
import hashlib
import os
import signal
import subprocess
import tempfile
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


class SubscriptionHttpTests(unittest.TestCase):
    def test_complete_caddy_template_adapts(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            header = root / "traffic-header.caddy"
            header.write_text(RENDERED["traffic-header.caddy"])
            config = root / "Caddyfile"
            config.write_text(RENDERED["Caddyfile"].replace(
                "/etc/clash-subscription/traffic-header.caddy", str(header)))
            result = subprocess.run([os.environ["CADDY_BIN"], "adapt", "--config", str(config),
                                     "--adapter", "caddyfile"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_traffic_reload_preserves_yaml_and_private_path(self):
        body = RENDERED["clash.yaml"].encode()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "clash.yaml").write_bytes(body)
            header = root / "traffic-header.caddy"
            header.write_text('Subscription-Userinfo "upload=900; download=400; total=2199023255552; expire=0"\n')
            config = root / "Caddyfile"
            config.write_text('''{
admin off
persist_config off
auto_https off
}
http://127.0.0.1:18796 {
bind 127.0.0.1
handle /test-private-subscription {
root * "ROOT"
rewrite * /clash.yaml
header {
import "HEADER"
profile-update-interval 1
}
file_server
}
handle {
respond 404
}
}
'''.replace('ROOT', str(root)).replace('HEADER', str(header)))
            log = (root / "log").open("w+")
            process = subprocess.Popen([os.environ["CADDY_BIN"], "run", "--config", str(config),
                                        "--adapter", "caddyfile"], stdout=log, stderr=log)
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                url = "http://127.0.0.1:18796/test-private-subscription"
                for _ in range(50):
                    try:
                        first = opener.open(url, timeout=1)
                        break
                    except urllib.error.URLError:
                        time.sleep(.05)
                else:
                    log.seek(0)
                    self.fail(log.read())
                self.assertEqual(first.headers["Subscription-Userinfo"],
                                 "upload=900; download=400; total=2199023255552; expire=0")
                self.assertEqual(first.headers["profile-update-interval"], "1")
                self.assertEqual(hashlib.sha256(first.read()).digest(), hashlib.sha256(body).digest())
                header.write_text('Subscription-Userinfo "upload=1900; download=1400; total=2199023255552; expire=0"\n')
                os.kill(process.pid, signal.SIGUSR1)
                for _ in range(50):
                    after = opener.open(url, timeout=1)
                    if "upload=1900; download=1400" in after.headers["Subscription-Userinfo"]:
                        break
                    time.sleep(.05)
                else:
                    self.fail("Updated header was not loaded")
                self.assertEqual(after.read(), body)
                with self.assertRaises(urllib.error.HTTPError) as denied:
                    opener.open("http://127.0.0.1:18796/wrong-path", timeout=1)
                self.assertEqual(denied.exception.code, 404)
                denied.exception.close()
            finally:
                process.terminate()
                process.wait(timeout=5)
                log.close()


if __name__ == "__main__":
    unittest.main()
