#!/usr/bin/env python3
"""Report provider/backend readiness for Evidence Scout.

The regular API validators answer "does this specific integration work?".
This doctor answers a different setup question: "for each source family, what
route is currently usable, and what fallbacks exist?"
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_DIR = ROOT / "scripts" / "validate_apis"
sys.path.insert(0, str(VALIDATOR_DIR))

from common import get_secret, http_get, now_iso, write_json, with_query  # noqa: E402


OUTPUT_DIR = ROOT / "research" / "evidence-scout" / "provider-doctor"
VALIDATION_SUMMARY = ROOT / "research" / "evidence-scout" / "api-validation" / "all.summary.json"
VALIDATION_DIR = ROOT / "research" / "evidence-scout" / "api-validation"


def latest_validation_statuses() -> dict[str, dict[str, Any]]:
    statuses: dict[str, dict[str, Any]] = {}
    for path in VALIDATION_DIR.glob("*.summary.json"):
        if path.name == "all.summary.json":
            continue
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(item, dict) and item.get("provider"):
            statuses[str(item["provider"])] = item
    try:
        data = json.loads(VALIDATION_SUMMARY.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return statuses
    if not isinstance(data, list):
        return statuses
    statuses.update({str(item.get("provider")): item for item in data if isinstance(item, dict) and item.get("provider")})
    return statuses


VALIDATION_PROVIDER_ALIASES = {
    "reddit_api": "reddit",
    "scrapecreators_reddit": "scrapecreators",
    "serpapi_google_trends": "serpapi_google_trends",
    "dataforseo_google_trends": "dataforseo_google_trends",
    "firecrawl_search": "firecrawl",
    "serper_search": "serper",
    "brave_search": "brave_search",
    "serper_bilibili_v2ex_site_search": "serper",
    "firecrawl_bilibili_v2ex_site_search": "firecrawl",
    "brave_bilibili_v2ex_site_search": "brave_search",
    "serper_china_web": "serper",
    "firecrawl_china_web": "firecrawl",
    "brave_china_web": "brave_search",
    "crawl4ai_cli": "crawl4ai",
    "markitdown_cli": "markitdown",
    "scrapling_cli": "scrapling",
    "youtube_data_api": "youtube",
    "scrapecreators_youtube": "scrapecreators",
    "x_api": "x",
    "xai_x_search": "xai_x_search",
    "scrapecreators_social": "scrapecreators",
    "scrapecreators_china_social": "scrapecreators",
    "sonar": "sonar",
    "itunes_reviews_rss": "itunes_reviews",
    "hn_algolia": "hn",
    "github_search_anonymous": "github",
    "google_autocomplete": "google_autocomplete",
}


@dataclass
class BackendStatus:
    name: str
    status: str
    message: str
    kind: str = "api"
    risk: str = "normal"

    @property
    def usable(self) -> bool:
        return self.status == "ok"


def apply_live_validation(candidate: BackendStatus, latest: dict[str, dict[str, Any]]) -> BackendStatus:
    provider = VALIDATION_PROVIDER_ALIASES.get(candidate.name)
    if not provider or provider not in latest:
        if candidate.kind == "api" and candidate.status == "ok":
            return BackendStatus(
                name=candidate.name,
                status="credentials_present",
                message="Credentials are present, but no live validator result was found. Run scripts/validate_apis/run_all.py before relying on this route.",
                kind=candidate.kind,
                risk=candidate.risk,
            )
        return candidate
    result = latest[provider]
    status = str(result.get("status") or "failed")
    detail_parts = [f"Latest live validator `{provider}` returned `{status}`"]
    if result.get("http_status"):
        detail_parts.append(f"HTTP {result['http_status']}")
    if result.get("required_env"):
        detail_parts.append("requires " + ", ".join(result["required_env"]))
    return BackendStatus(
        name=candidate.name,
        status=status,
        message="; ".join(detail_parts),
        kind=candidate.kind,
        risk=candidate.risk,
    )


def _env_backend(name: str, required_env: list[str], *, risk: str = "normal") -> BackendStatus:
    missing = [env for env in required_env if not get_secret(env)[1]]
    if missing:
        return BackendStatus(
            name=name,
            status="missing_credentials",
            message=f"Missing env: {', '.join(missing)}",
            kind="api",
            risk=risk,
        )
    return BackendStatus(name=name, status="ok", message="Required credentials are present", kind="api", risk=risk)


def _command_backend(name: str, cmd: str, args: list[str] | None = None, *, risk: str = "normal", timeout: int = 10) -> BackendStatus:
    path = shutil.which(cmd)
    if not path:
        return BackendStatus(name=name, status="missing_cli", message=f"`{cmd}` is not on PATH", kind="cli", risk=risk)
    try:
        proc = subprocess.run(
            [path, *(args or ["--version"])],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return BackendStatus(name=name, status="timeout", message=f"`{cmd}` probe timed out", kind="cli", risk=risk)
    except OSError as exc:
        return BackendStatus(name=name, status="broken_cli", message=f"`{cmd}` exists but cannot execute: {exc}", kind="cli", risk=risk)
    if proc.returncode in {126, 127}:
        return BackendStatus(name=name, status="broken_cli", message=f"`{cmd}` exists but is not executable", kind="cli", risk=risk)
    if proc.returncode != 0:
        output = (proc.stderr or proc.stdout or "").strip().splitlines()
        detail = output[-1] if output else f"exit {proc.returncode}"
        return BackendStatus(name=name, status="warn", message=f"`{cmd}` ran but returned {detail}", kind="cli", risk=risk)
    return BackendStatus(name=name, status="ok", message=f"`{cmd}` probe succeeded", kind="cli", risk=risk)


def _public_http_backend(name: str, url: str, params: dict[str, Any] | None = None) -> BackendStatus:
    response = http_get(with_query(url, params or {}), timeout=12)
    if response.get("ok"):
        return BackendStatus(name=name, status="ok", message="Public HTTP probe succeeded", kind="public_http")
    code = response.get("status_code")
    error = response.get("error") or ""
    return BackendStatus(
        name=name,
        status="network_blocked_or_sandboxed" if code is None else "failed",
        message=f"Public HTTP probe failed: {code or error}",
        kind="public_http",
    )


def _agent_reach_channel(channel: str) -> BackendStatus:
    path = shutil.which("agent-reach")
    if not path:
        return BackendStatus(
            name=f"agent_reach_{channel}",
            status="missing_cli",
            message="`agent-reach` is not installed",
            kind="cli",
            risk="login_or_cookie_backed",
        )
    try:
        proc = subprocess.run(
            [path, "doctor", "--json"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return BackendStatus(
            name=f"agent_reach_{channel}",
            status="failed",
            message=f"`agent-reach doctor --json` failed: {exc}",
            kind="cli",
            risk="login_or_cookie_backed",
        )
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return BackendStatus(
            name=f"agent_reach_{channel}",
            status="failed",
            message="`agent-reach doctor --json` returned non-JSON output",
            kind="cli",
            risk="login_or_cookie_backed",
        )
    item = data.get(channel) if isinstance(data, dict) else None
    if not isinstance(item, dict):
        return BackendStatus(
            name=f"agent_reach_{channel}",
            status="unsupported",
            message=f"Agent Reach did not report channel `{channel}`",
            kind="cli",
            risk="login_or_cookie_backed",
        )
    return BackendStatus(
        name=f"agent_reach_{channel}",
        status=item.get("status") or "failed",
        message=item.get("message") or "No message",
        kind="cli",
        risk="login_or_cookie_backed",
    )


def provider_groups() -> dict[str, list[BackendStatus]]:
    return {
        "reddit": [
            _env_backend("reddit_api", ["REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"]),
            _agent_reach_channel("reddit"),
            _env_backend("scrapecreators_reddit", ["SCRAPE_CREATORS_API_KEY"], risk="paid_credits"),
        ],
        "google_trends": [
            _env_backend("serpapi_google_trends", ["SERPAPI_API_KEY"], risk="paid_or_quota_limited"),
            _env_backend("dataforseo_google_trends", ["DATAFORSEO_LOGIN", "DATAFORSEO_PASSWORD"], risk="paid_credits"),
        ],
        "web_search": [
            _env_backend("serper_search", ["SERPER_DEV_API_KEY"], risk="paid_credits_google_only"),
            _env_backend("firecrawl_search", ["FIRECRAWL_API_KEY_HGINVESTOR"], risk="paid_or_quota_limited"),
            _env_backend("brave_search", ["BRAVE_SEARCH_API_KEY"], risk="paid_or_quota_limited"),
        ],
        "local_extraction": [
            _command_backend("crawl4ai_cli", "crwl", ["--help"], risk="local_optional"),
            _command_backend("markitdown_cli", "markitdown", ["--help"], risk="local_optional"),
            _command_backend("scrapling_cli", "scrapling", ["--help"], risk="explicit_hard_page_fallback"),
        ],
        "youtube": [
            _env_backend("youtube_data_api", ["YOUTUBE_API_KEY"]),
            _env_backend("scrapecreators_youtube", ["SCRAPE_CREATORS_API_KEY"], risk="paid_credits"),
            _command_backend("yt_dlp_cli", "yt-dlp", ["--version"]),
        ],
        "social": [
            _env_backend("x_api", ["X_BEARER_TOKEN"], risk="paid_or_quota_limited"),
            _env_backend("xai_x_search", ["GROK_API_KEY"], risk="model_tool_costs"),
            _env_backend("scrapecreators_social", ["SCRAPE_CREATORS_API_KEY"], risk="paid_credits"),
        ],
        "app_store": [
            _env_backend("sonar", ["SONAR_API_KEY"], risk="paid_credits"),
            _public_http_backend(
                "itunes_reviews_rss",
                "https://itunes.apple.com/us/rss/customerreviews/id=284882215/sortBy=mostRecent/json",
                {"page": 1},
            ),
        ],
        "founder_community": [
            _public_http_backend(
                "hn_algolia",
                "https://hn.algolia.com/api/v1/search",
                {"query": "startup pain", "tags": "story", "hitsPerPage": 1},
            ),
            _public_http_backend(
                "google_autocomplete",
                "https://suggestqueries.google.com/complete/search",
                {"client": "firefox", "hl": "en", "gl": "us", "q": "why is my accountant"},
            ),
        ],
        "github_issues": [
            _public_http_backend(
                "github_search_anonymous",
                "https://api.github.com/search/issues",
                {"q": "reporting workaround type:issue", "per_page": 1},
            ),
            _env_backend("github_search_token", ["GITHUB_TOKEN"], risk="free_optional_higher_rate"),
        ],
        "china_public_native": [
            _public_http_backend(
                "bilibili_public_search",
                "https://api.bilibili.com/x/web-interface/search/type",
                {"search_type": "video", "keyword": "AI", "page": 1, "page_size": 1},
            ),
            _public_http_backend("v2ex_public_hot", "https://www.v2ex.com/api/topics/hot.json"),
            _agent_reach_channel("bilibili"),
        ],
        "china_public_search": [
            _env_backend("serper_bilibili_v2ex_site_search", ["SERPER_DEV_API_KEY"], risk="paid_credits_google_only"),
            _env_backend("brave_bilibili_v2ex_site_search", ["BRAVE_SEARCH_API_KEY"], risk="paid_or_quota_limited"),
            _env_backend("firecrawl_bilibili_v2ex_site_search", ["FIRECRAWL_API_KEY_HGINVESTOR"], risk="paid_or_quota_limited"),
        ],
        "china_social": [
            _agent_reach_channel("xiaohongshu"),
            _env_backend("scrapecreators_china_social", ["SCRAPE_CREATORS_API_KEY"], risk="paid_credits"),
        ],
        "china_web": [
            _env_backend("serper_china_web", ["SERPER_DEV_API_KEY"], risk="paid_credits_google_only"),
            _env_backend("firecrawl_china_web", ["FIRECRAWL_API_KEY_HGINVESTOR"], risk="paid_or_quota_limited"),
            _env_backend("brave_china_web", ["BRAVE_SEARCH_API_KEY"], risk="paid_or_quota_limited"),
        ],
    }


def summarize(groups: dict[str, list[BackendStatus]]) -> dict[str, Any]:
    latest = latest_validation_statuses()
    summary: dict[str, Any] = {
        "generated_at": now_iso(),
        "live_validation_source": str(VALIDATION_SUMMARY.relative_to(ROOT)) if latest else None,
        "source_families": {},
        "needs_user_attention": [],
    }
    if not latest:
        summary["needs_user_attention"].append(
            "No live API validation summary found. Run `python3 scripts/validate_apis/run_all.py` before relying on provider doctor routing."
        )
    else:
        try:
            age_days = max(0.0, (time.time() - VALIDATION_SUMMARY.stat().st_mtime) / 86400)
        except OSError:
            age_days = None
        if age_days is None or age_days > 14:
            summary["validation_age_days"] = round(age_days, 1) if age_days is not None else "unknown"
            summary["needs_user_attention"].append(
                f"Live validation summaries are {summary['validation_age_days']} days old. Re-run `python3 scripts/validate_apis/run_all.py`; stale results can misroute fallbacks."
            )
    for family, candidates in groups.items():
        candidates = [apply_live_validation(candidate, latest) for candidate in candidates]
        active = next((candidate for candidate in candidates if candidate.usable), None)
        statuses = [asdict(candidate) for candidate in candidates]
        optional_family = family in {"local_extraction", "china_public_native"}
        family_summary = {
            "status": "ok" if active else "optional_unavailable" if optional_family else "unavailable",
            "active_backend": active.name if active else None,
            "candidates": statuses,
        }
        summary["source_families"][family] = family_summary
        if not active and not optional_family:
            summary["needs_user_attention"].append(
                f"`{family}` has no usable backend. Configure one candidate or avoid interpreting this source family."
            )
    return summary


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Evidence Scout Provider Doctor",
        "",
        f"- Generated at: {summary['generated_at']}",
        "",
        "## Source Families",
        "",
    ]
    for family, item in summary["source_families"].items():
        lines.append(f"### {family}")
        lines.append("")
        lines.append(f"- Status: `{item['status']}`")
        lines.append(f"- Active backend: `{item['active_backend'] or 'none'}`")
        lines.append("- Candidates:")
        for candidate in item["candidates"]:
            lines.append(
                f"  - `{candidate['name']}`: `{candidate['status']}` "
                f"({candidate['kind']}, risk: `{candidate['risk']}`) - {candidate['message']}"
            )
        lines.append("")
    if summary["needs_user_attention"]:
        lines.extend(["## Needs User Attention", ""])
        lines.extend(f"- {alert}" for alert in summary["needs_user_attention"])
        lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Evidence Scout provider and backend readiness.")
    parser.add_argument("--json", action="store_true", help="Print JSON only.")
    parser.add_argument("--out-dir", default=str(OUTPUT_DIR), help="Directory for doctor summary outputs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(provider_groups())
    write_json(out_dir / "doctor.summary.json", summary)
    (out_dir / "doctor.md").write_text(render_markdown(summary), encoding="utf-8")
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(render_markdown(summary))
    return 0 if not summary["needs_user_attention"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
