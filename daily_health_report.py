import json
import os
import time
import urllib.parse
import urllib.request

import requests
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")
GITHUB_API = "https://api.github.com"
AUTO_REPAIR = os.getenv("AUTO_REPAIR", "true").lower() not in {"0", "false", "off"}
REPAIR_POLL_ATTEMPTS = int(os.getenv("REPAIR_POLL_ATTEMPTS", "8"))
REPAIR_WAIT_SECONDS = int(os.getenv("REPAIR_WAIT_SECONDS", "15"))


@dataclass(frozen=True)
class WorkflowCheck:
    repo: str
    workflow_file: str
    labels: tuple[str, ...]
    max_age_hours: int
    ref: str = "main"


@dataclass(frozen=True)
class CheckResult:
    status: str
    detail: str
    run_id: int | None = None

    @property
    def ok(self):
        return self.status in {"healthy", "recovered", "repairing"}


CHECKS = (
    WorkflowCheck(
        "ryoma1108/touraku-auto",
        "latest_update.yml",
        ("騰落レシオ通知", "騰落レシオWeb取得", "日経平均OHLC取得"),
        96,
    ),
    WorkflowCheck(
        "ryoma1108/nikkei-dividend-yield-alert",
        "run.yml",
        ("高配当株通知",),
        96,
    ),
    WorkflowCheck(
        "ryoma1108/instagram-insights-auto",
        "run.yml",
        ("Instagramインサイト",),
        36,
    ),
    WorkflowCheck(
        "ryoma1108/nikkei-data-auto",
        "run.yml",
        ("日経指標データ取得",),
        96,
    ),
)


def github_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ryoma1108-daily-health-report",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_request(url, method="GET", payload=None, timeout=20):
    data = None
    headers = github_headers()
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read()
        return json.loads(body) if body else {}


def latest_run(check):
    workflow = urllib.parse.quote(check.workflow_file, safe="")
    url = (
        f"{GITHUB_API}/repos/{check.repo}/actions/workflows/"
        f"{workflow}/runs?per_page=1"
    )
    data = github_request(url)
    runs = data.get("workflow_runs", [])
    return runs[0] if runs else None


def parse_github_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def evaluate_run(check, run, now=None):
    now = now or datetime.now(timezone.utc)
    if not run:
        return CheckResult("missing", "実行履歴なし")

    run_id = run.get("id")
    status = run.get("status") or "unknown"
    if status in {"queued", "in_progress", "waiting", "pending", "requested"}:
        return CheckResult("running", "現在実行中", run_id)

    finished_at = parse_github_datetime(run["updated_at"])
    age_hours = (now - finished_at).total_seconds() / 3600
    conclusion = run.get("conclusion") or "unknown"
    finished_jst = finished_at.astimezone(JST).strftime("%m/%d %H:%M")

    if conclusion != "success":
        return CheckResult(
            "failed",
            f"失敗（{conclusion}・{finished_jst}）",
            run_id,
        )
    if age_hours > check.max_age_hours:
        return CheckResult(
            "stale",
            f"更新停止の疑い（最終成功 {finished_jst}）",
            run_id,
        )
    return CheckResult("healthy", f"正常（最終成功 {finished_jst}）", run_id)


def evaluate_check(check, now=None):
    result = evaluate_run(check, latest_run(check), now=now)
    return result.ok, result.detail


def trigger_repair(check, result):
    if result.status == "failed" and result.run_id:
        url = (
            f"{GITHUB_API}/repos/{check.repo}/actions/runs/"
            f"{result.run_id}/rerun"
        )
        github_request(url, method="POST")
        return "失敗した処理を再実行"

    workflow = urllib.parse.quote(check.workflow_file, safe="")
    url = (
        f"{GITHUB_API}/repos/{check.repo}/actions/workflows/"
        f"{workflow}/dispatches"
    )
    github_request(url, method="POST", payload={"ref": check.ref})
    return "停止した処理を新しく実行"


def check_with_auto_repair(check, now=None):
    now = now or datetime.now(timezone.utc)
    initial = evaluate_run(check, latest_run(check), now=now)
    if initial.status == "healthy":
        return initial
    if initial.status == "running":
        return CheckResult("repairing", "処理実行中（重複実行なし）", initial.run_id)
    if not AUTO_REPAIR:
        return initial

    try:
        repair_action = trigger_repair(check, initial)
    except Exception as error:
        return CheckResult(
            "repair_failed",
            f"{initial.detail}／自動再実行できず（{type(error).__name__}）",
            initial.run_id,
        )

    last_result = initial
    for _ in range(REPAIR_POLL_ATTEMPTS):
        if REPAIR_WAIT_SECONDS:
            time.sleep(REPAIR_WAIT_SECONDS)
        try:
            last_result = evaluate_run(check, latest_run(check), now=now)
        except Exception:
            continue
        if last_result.status == "healthy":
            return CheckResult(
                "recovered",
                f"自動再実行で復旧（{repair_action}）",
                last_result.run_id,
            )

    if last_result.status == "running":
        return CheckResult(
            "repairing",
            f"自動修復を開始・現在実行中（{repair_action}）",
            last_result.run_id,
        )
    return CheckResult(
        "repair_failed",
        f"自動再実行後も未復旧（{last_result.detail}）",
        last_result.run_id,
    )


def result_mark(result):
    if result.status in {"healthy", "recovered"}:
        return "✅"
    if result.status == "repairing":
        return "△"
    return "❌"


def build_report(now=None):
    now = now or datetime.now(timezone.utc)
    lines = [
        "【7システム毎日健康診断】",
        now.astimezone(JST).strftime("%Y/%m/%d %H:%M"),
        "",
        "△ VIX通知",
        "TradingViewの発火待ちのため外部からの自動判定対象外",
    ]
    all_ok = True
    repaired = False
    repairing = False

    for check in CHECKS:
        try:
            result = check_with_auto_repair(check, now=now)
        except Exception as error:
            result = CheckResult(
                "repair_failed",
                f"確認エラー（{type(error).__name__}）",
            )
        all_ok = all_ok and result.ok
        repaired = repaired or result.status == "recovered"
        repairing = repairing or result.status == "repairing"
        mark = result_mark(result)
        for label in check.labels:
            lines.append(f"{mark} {label}: {result.detail}")

    lines.append("")
    if not all_ok:
        lines.append("自動再実行でも直らない項目があります。手動確認が必要です。")
    elif repairing:
        lines.append("自動修復を開始しました。現在、完了を待っています。")
    elif repaired:
        lines.append("異常を検知しましたが、自動再実行で復旧しました。")
    else:
        lines.append("GitHub側の6項目はすべて正常です。")
    lines.append("※VIX通知は、実際のシグナル発生時のLINE到着で確認します。")
    return "\n".join(lines), all_ok


def send_line(message):
    webhook_url = os.environ["GAS_WEBHOOK_URL"]
    payload = {"action": "send_line", "message": message}

    last_error = None
    for attempt in range(3):
        try:
            response = requests.post(
                webhook_url,
                data=json.dumps(payload, ensure_ascii=False),
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            response.raise_for_status()
            response_body = response.text
            if "Script function not found" in response_body:
                raise RuntimeError(
                    f"GAS error response: {response_body[:200]}"
                )
            return response_body
        except (requests.RequestException, RuntimeError) as error:
            last_error = error
            if attempt < 2:
                time.sleep(2**attempt)
    raise RuntimeError(f"LINE通知に失敗しました: {last_error}")

def main():
    report, all_ok = build_report()
    print(report)
    print(send_line(report))
    if not all_ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
