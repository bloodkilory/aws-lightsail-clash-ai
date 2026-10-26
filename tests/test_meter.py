import importlib.util
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("meter", Path(__file__).with_name("meter.py"))
meter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(meter)


class MetricApi:
    def __init__(self, start, end, incoming, outgoing):
        self.start, self.end = start, end
        self.data = {"NetworkIn": incoming, "NetworkOut": outgoing}

    def get_instance_metric_data(self, **args):
        expected = dict(instanceName="personal-proxy-sg", metricName=args["metricName"],
                        period=3600, startTime=self.start, endTime=self.end,
                        unit="Bytes", statistics=["Sum"])
        if args != expected:
            raise AssertionError(args)
        points = self.data[args["metricName"]]
        if isinstance(points, Exception):
            raise points
        return {"metricName": args["metricName"], "metricData": points}


def point(value, stamp):
    return {"sum": value, "timestamp": stamp, "unit": "Bytes"}


class MeterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.header = Path(self.tmp.name) / "header.caddy"
        self.state = Path(self.tmp.name) / "state.json"
        self.start = datetime(2026, 10, 1, tzinfo=timezone.utc)
        self.now = datetime(2026, 10, 26, 2, 15, tzinfo=timezone.utc)

    def update(self, api, now=None):
        return meter.update(api, now or self.now, self.header, self.state)

    def test_sums_aws_network_in_and_out_without_averaging(self):
        api = MetricApi(self.start, self.now,
                        [point(100, self.start), point(300, self.start)],
                        [point(900, self.start)])
        value = self.update(api)
        self.assertEqual(value["used_bytes"], 1300)
        self.assertEqual(self.header.read_text(),
                         'Subscription-Userinfo "upload=900; download=400; total=2199023255552; expire=0"\n')

    def test_year_boundary_queries_only_new_utc_month(self):
        self.header.write_text("previous December counter")
        now = datetime(2027, 1, 1, 0, 2, tzinfo=timezone.utc)
        start = datetime(2027, 1, 1, tzinfo=timezone.utc)
        value = self.update(MetricApi(start, now, [], []), now)
        self.assertEqual(value["month"], "2027-01")
        self.assertEqual(value["used_bytes"], 0)

    def test_outbound_api_failure_leaves_previous_files_untouched(self):
        self.header.write_text("previous header")
        self.state.write_text("previous state")
        api = MetricApi(self.start, self.now, [point(10, self.start)], RuntimeError("AWS unavailable"))
        with self.assertRaises(RuntimeError):
            self.update(api)
        self.assertEqual(self.header.read_text(), "previous header")
        self.assertEqual(self.state.read_text(), "previous state")

    def test_missing_old_month_data_does_not_publish_false_zero(self):
        self.header.write_text("previous header")
        with self.assertRaises(ValueError):
            self.update(MetricApi(self.start, self.now, [], []))
        self.assertEqual(self.header.read_text(), "previous header")

    def test_overage_is_not_capped_to_allowance(self):
        value = self.update(MetricApi(self.start, self.now,
                                      [point(2199023255552, self.start)], [point(4096, self.start)]))
        self.assertEqual(value["used_bytes"], 2199023259648)

    def test_malformed_data_does_not_overwrite_old_header(self):
        self.header.write_text("previous header")
        with self.assertRaises(ValueError):
            self.update(MetricApi(self.start, self.now,
                                  [point(-1, self.start)], [point(5, self.start)]))
        self.assertEqual(self.header.read_text(), "previous header")


if __name__ == "__main__":
    unittest.main()
