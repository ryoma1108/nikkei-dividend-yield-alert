import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import daily_health_report


class DailyHealthReportTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 28, 0, 15, tzinfo=timezone.utc)

    def make_run(self, conclusion="success", age_hours=1):
        updated_at = self.now - timedelta(hours=age_hours)
        return {
            "conclusion": conclusion,
            "updated_at": updated_at.isoformat().replace("+00:00", "Z"),
        }

    @patch("daily_health_report.latest_completed_run")
    def test_successful_fresh_run_is_healthy(self, latest_run):
        latest_run.return_value = self.make_run()
        ok, detail = daily_health_report.evaluate_check(
            daily_health_report.CHECKS[0], now=self.now
        )
        self.assertTrue(ok)
        self.assertIn("正常", detail)

    @patch("daily_health_report.latest_completed_run")
    def test_failed_run_is_unhealthy(self, latest_run):
        latest_run.return_value = self.make_run(conclusion="failure")
        ok, detail = daily_health_report.evaluate_check(
            daily_health_report.CHECKS[0], now=self.now
        )
        self.assertFalse(ok)
        self.assertIn("失敗", detail)

    @patch("daily_health_report.latest_completed_run")
    def test_stale_run_is_unhealthy(self, latest_run):
        latest_run.return_value = self.make_run(age_hours=100)
        ok, detail = daily_health_report.evaluate_check(
            daily_health_report.CHECKS[0], now=self.now
        )
        self.assertFalse(ok)
        self.assertIn("更新停止", detail)

    @patch("daily_health_report.evaluate_check")
    def test_report_contains_all_seven_labels(self, evaluate):
        evaluate.return_value = (True, "正常")
        report, all_ok = daily_health_report.build_report(now=self.now)
        self.assertTrue(all_ok)
        expected = (
            "VIX通知",
            "騰落レシオ通知",
            "高配当株通知",
            "Instagramインサイト",
            "騰落レシオWeb取得",
            "日経指標データ取得",
            "日経平均OHLC取得",
        )
        for label in expected:
            self.assertIn(label, report)


if __name__ == "__main__":
    unittest.main()
