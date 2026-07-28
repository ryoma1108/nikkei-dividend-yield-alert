import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


JST = ZoneInfo("Asia/Tokyo")
GITHUB_API = "https://api.github.com"


@dataclass(frozen=True)
class WorkflowCheck:
    repo: str
    workflow_file: str
    labels: tuple[str, ...]
    max_age_hours: int


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


def load_json(url, timeout=20):
    request = urllib.request.Request(url, headers=github_headers())
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def latest_completed_run(check):
    url = (
        f"{GITHUB_API}/repos/{check.repo}/actions/workflows/"
        f"{check.workflow_file}/runs?status=completed&per_page=1"
    )
    data = load_json(url)
    runs = data.get("workflow_runs", [])
    return runs[0] if runs else None


def parse_github_datetime(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def evaluate_check(check, now=None):
    now = now or datetime.now(timezone.utc)
    run = latest_completed_run(check)
    if not run:
        return False, "実行履歴なし"

    finished_at = parse_github_datetime(run["updated_at"])
    age_hours = (now - finished_at).total_seconds() / 3600
    conclusion = run.get("conclusion") or "unknown"
    finished_jst = finished_at.astimezone(JST).strftime("%m/%d %H:%M")

    if conclusion != "success":
        return False, f"失敗（{finished_jst}）"
    if age_hours > check.max_age_hours:
        return False, f"更新停止の疑い（最終成功 {finished_jst}）"
    return True, f"正常（最終成功 {finished_jst}）"


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

    for check in CHECKS:
        try:
            ok, detail = evaluate_check(check, now=now)
        except Exception as error:
            ok = False
            detail = f"確認エラー（{type(error).__name__}）"
        all_ok = all_ok and ok
        mark = "✅" if ok else "❌"
        for label in check.labels:
            lines.append(f"{mark} {label}: {detail}")

    lines.extend(
        [
            "",
            (
                "GitHub側の6項目はすべて正常です。"
                if all_ok
                else "要確認の項目があります。Codexで原因を確認してください。"
            ),
            "※VIX通知は、実際のシグナル発生時のLINE到着で確認します。",
        ]
    )
    return "\n".join(lines), all_ok


def send_line(message):
    webhook_url = os.environ["GAS_WEBHOOK_URL"]
    body = json.dumps(
        {"action": "send_line", "message": message},
        ensure_ascii=False,
    ).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                response_body = response.read().decode("utf-8", errors="replace")
                if not 200 <= response.status < 300:
                    raise RuntimeError(f"HTTP {response.status}: {response_body}")
                return response_body
        except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
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
