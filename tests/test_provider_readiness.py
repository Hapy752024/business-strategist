"""Provider checks must reflect content access and the effective query."""
import importlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/validate_apis"))
sys.path.insert(0, str(ROOT / "scripts"))


def test_query_cli_accepts_both_forms_and_rejects_missing_value(monkeypatch):
    from common import cli_arg
    for argv in (["validator", "--query", "PKV GKV"], ["validator", "--query=PKV GKV"]):
        monkeypatch.setattr(sys, "argv", argv)
        assert cli_arg("query", "default") == "PKV GKV"
    monkeypatch.setattr(sys, "argv", ["validator", "--query"])
    try:
        cli_arg("query", "default")
    except ValueError as exc:
        assert "requires a value" in str(exc)
    else:
        raise AssertionError("missing query was silently defaulted")


def test_reddit_token_success_does_not_hide_post_failure(monkeypatch):
    reddit = importlib.import_module("validate_reddit")
    monkeypatch.setattr(reddit, "get_secret", lambda name: (name, "dummy"))
    monkeypatch.setattr(reddit, "http_post", lambda *a, **k: {"ok": True, "status_code": 200, "body": {"access_token": "dummy"}})
    monkeypatch.setattr(reddit, "cli_arg", lambda *_: "PKV GKV")
    calls = iter([{"ok": True, "status_code": 200, "body": {"data": {"children": []}}},
                  {"ok": False, "status_code": 403, "body": {"message": "denied"}}])
    monkeypatch.setattr(reddit, "http_get", lambda *a, **k: next(calls))
    captured = {}
    monkeypatch.setattr(reddit, "finish", lambda _provider, summary, _raw: captured.update(summary) or 0)
    assert reddit.main() == 0
    assert captured["status"] != "ok" and captured["endpoint_statuses"]["posts"] != "ok"
    assert captured["query"] == "PKV GKV"


def test_youtube_search_success_does_not_hide_comment_failure(monkeypatch):
    youtube = importlib.import_module("validate_youtube")
    monkeypatch.setattr(youtube, "get_secret", lambda *_: ("YOUTUBE_API_KEY", "dummy"))
    monkeypatch.setattr(youtube, "cli_arg", lambda *_: "PKV GKV")
    monkeypatch.setattr(youtube, "transcript_probe", lambda: ("not_run", 0))
    calls = iter([{"ok": True, "status_code": 200, "body": {"items": [{"id": {"videoId": "v1"}}]}},
                  {"ok": False, "status_code": 403, "body": {"message": "comments disabled"}}])
    monkeypatch.setattr(youtube, "http_get", lambda *_: next(calls))
    captured = {}
    monkeypatch.setattr(youtube, "finish", lambda _provider, summary, _raw: captured.update(summary) or 0)
    youtube.main()
    assert captured["status"] == "partial" and captured["comment_fetch_status"] != "ok"
    assert captured["video_count"] == 1


def test_selected_provider_cli_rejects_unknown_flag_without_network():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/validate_apis/run_all.py"), "--unknown"],
                            capture_output=True, text=True)
    assert result.returncode == 2 and "unrecognized arguments" in result.stderr


def test_firecrawl_cli_wrapper_uses_required_account_not_generic(monkeypatch):
    wrapper = importlib.import_module("firecrawl_project")
    monkeypatch.setattr(wrapper, "get_secret", lambda *_: ("FIRECRAWL_API_KEY_HGINVESTOR", "required-dummy"))
    monkeypatch.setenv("FIRECRAWL_API_KEY", "wrong-dummy")
    monkeypatch.setattr(sys, "argv", ["firecrawl_project.py", "search", "PKV"])
    seen = {}
    monkeypatch.setattr(wrapper.subprocess, "run", lambda command, **kw: seen.update(command=command, env=kw["env"]) or type("Result", (), {"returncode": 0})())
    assert wrapper.main() == 0
    assert seen["command"] == ["firecrawl", "search", "PKV"]
    assert seen["env"]["FIRECRAWL_API_KEY"] == "required-dummy"
