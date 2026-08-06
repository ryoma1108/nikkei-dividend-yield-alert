import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import daily_health_report


class DailyHealthReportTest(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 28, 0, 15, tzinfo=timezone.utc)

    def make_run(self, conclusion="success", age_hours=1, status="completed", run_id=1):
        updated_at = self.now - timedelta(hours=age_hours)
        return {
            "id": run_id,
            "status": status,
            "conclusion": conclusion,
            "updated_at": updated_at.isoformat().replace("+00:00", "Z"),
        }

    def test_successful_fresh_run_is_healthy(self):
        result = daily_health_report.evaluate_run(
            daily_health_report.CHECKS[0],
            self.make_run(),
            now=self.now,
        )
        self.assertEqual("healthy", result.status)
        self.assertIn("正常", result.detail)

    def test_failed_run_is_unhealthy(self):
        result = daily_health_report.evaluate_run(
            daily_health_report.CHECKS[0],
            self.make_run(conclusion="failure"),
            now=self.now,
        )
        self.assertEqual("failed", result.status)
        self.assertIn("失敗", result.detail)

    def test_stale_run_is_unhealthy(self):
        result = daily_health_report.evaluate_run(
            daily_health_report.CHECKS[0],
            self.make_run(age_hours=100),
            now=self.now,
        )
        self.assertEqual("stale", result.status)
        self.assertIn("更新停止", result.detail)

    @patch("daily_health_report.github_request")
    def test_failed_run_triggers_rerun(self, request):
        result = daily_health_report.CheckResult("failed", "失敗", 123)
        action = daily_health_report.trigger_repair(
            daily_health_report.CHECKS[0],
            result,
        )
        self.assertIn("再実行", action)
        request.assert_called_once_with(
            f"{daily_health_report.GITHUB_API}/repos/ryoma1108/touraku-auto/actions/runs/123/rerun",
            method="POST",
        )

    @patch("daily_health_report.github_request")
    def test_stale_run_triggers_workflow_dispatch(self, request):
        result = daily_health_report.CheckResult("stale", "停止", 123)
        daily_health_report.trigger_repair(daily_health_report.CHECKS[0], result)
        request.assert_called_once_with(
            f"{daily_health_report.GITHUB_API}/repos/ryoma1108/touraku-auto/actions/workflows/latest_update.yml/dispatches",
            method="POST",
            payload={"ref": "main"},
        )

    @patch("daily_health_report.REPAIR_WAIT_SECONDS", 0)
    @patch("daily_health_report.latest_run")
    @patch("daily_health_report.trigger_repair")
    def test_auto_repair_reports_recovery(self, trigger, latest):
        latest.side_effect = [
            self.make_run(conclusion="failure", run_id=10),
            self.make_run(conclusion="success", run_id=10),
        ]
        trigger.return_value = "失敗した処理を再実行"
        result = daily_health_report.check_with_auto_repair(
            daily_health_report.CHECKS[0],
            now=self.now,
        )
        self.assertEqual("recovered", result.status)
        self.assertIn("復旧", result.detail)

    @patch("daily_health_report.check_with_auto_repair")
    def test_report_contains_all_seven_labels(self, check):
        check.return_value = daily_health_report.CheckResult("healthy", "正常")
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


    @patch("daily_health_report.time.sleep")
    @patch("daily_health_report.requests.post")
    def test_send_line_returns_success_response(self, post, sleep):
        response = Mock()
        response.text = '{"ok":true}'
        post.return_value = response

        with patch.dict(
            os.environ,
            {"GAS_WEBHOOK_URL": "https://example.com/exec"},
        ):
            result = daily_health_report.send_line("health check")

        self.assertEqual('{"ok":true}', result)
        response.raise_for_status.assert_called_once()
        post.assert_called_once()

    @patch("daily_health_report.time.sleep")
    @patch("daily_health_report.requests.post")
    def test_send_line_rejects_apps_script_error_page(self, post, sleep):
        response = Mock()
        response.text = (
            "<title>Error</title>"
            "Script function not found: doGet"
        )
        post.return_value = response

        with patch.dict(
            os.environ,
            {"GAS_WEBHOOK_URL": "https://example.com/exec"},
        ):
            with self.assertRaisesRegex(RuntimeError, "LINE通知に失敗"):
                daily_health_report.send_line("health check")

        self.assertEqual(3, post.call_count)


if __name__ == "__main__":
    unittest.main()
