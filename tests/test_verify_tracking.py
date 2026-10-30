import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_tracking", ROOT / "scripts/marketing/verify_tracking.py")
vt = importlib.util.module_from_spec(spec); spec.loader.exec_module(vt)

META = {"report_scope": "events", "property": "site", "period_start": "2026-10-24", "period_end": "2026-10-30",
        "timezone": "UTC", "exported_at": "2026-10-31"}


def event(name, **kw):
    base = {"name": name, "trigger": "when it happens", "required_properties": [], "consent_category": "necessary",
            "destinations": ["ga4", "posthog"], "owner": "founder", "required_for_launch": True}
    return base | kw


def plan(tmp_path, *events):
    path = tmp_path / "plan.json"
    path.write_text(json.dumps({"schema_version": 1, "project_id": "demo", "events": list(events)}))
    return path


def export(tmp_path, rows, header="Event name,Event count"):
    path = tmp_path / "events.csv"
    path.write_text(header + "\n" + "\n".join(rows) + "\n")
    return path


def test_verify_tracking_reports_missing_event(tmp_path):
    p = plan(tmp_path, event("page_view"), event("generate_lead"))
    out = vt.verify(p, "ga4", export=export(tmp_path, ["page_view,120"]), metadata=META)
    by = {e["name"]: e for e in out["events"]}
    assert by["page_view"]["status"] == "observed" and by["page_view"]["count"] == 120
    assert by["generate_lead"]["status"] == "not_observed"
    assert out["verdict"] == "not_ready"
    assert any("generate_lead" in r for r in out["reasons"])


def test_unknown_never_counts_as_observed(tmp_path, monkeypatch):
    monkeypatch.setattr(vt.connections, "adc_path", lambda: None)
    out = vt.verify(plan(tmp_path, event("page_view")), "ga4", store=tmp_path / "s.json")
    assert out["events"][0]["status"] == "unknown"
    assert out["verdict"] == "not_ready"


def test_ready_only_when_all_launch_events_observed_with_properties(tmp_path):
    p = plan(tmp_path, event("generate_lead", required_properties=["form_id"]), event("scroll", required_for_launch=False))
    good = lambda *a, **k: {"generate_lead": {"count": 4, "props": {"form_id": True}}}
    out = vt.verify(p, "posthog", fetcher=good)
    assert out["verdict"] == "ready"
    bad = lambda *a, **k: {"generate_lead": {"count": 4, "props": {"form_id": False}}}
    out = vt.verify(p, "posthog", fetcher=bad)
    assert out["verdict"] == "not_ready" and out["events"][0]["properties"]["form_id"] == "missing"
    unknown_props = lambda *a, **k: {"generate_lead": {"count": 4, "props": {}}}
    out = vt.verify(p, "posthog", fetcher=unknown_props)
    assert out["verdict"] == "not_ready" and out["events"][0]["properties"]["form_id"] == "unknown"
    # optional (non-launch) event unobserved does not block
    only_optional_missing = vt.verify(plan(tmp_path, event("scroll", required_for_launch=False), event("a")), "posthog",
                                      fetcher=lambda *a, **k: {"a": {"count": 1, "props": {}}})
    assert only_optional_missing["verdict"] == "ready"


def test_missing_credentials_is_unconnected_with_owner_steps_and_no_network(tmp_path, monkeypatch):
    monkeypatch.setattr(vt.connections, "adc_path", lambda: None)
    def boom(*a, **k): raise AssertionError("network call attempted")
    monkeypatch.setattr(vt.connections, "google_request", boom)
    monkeypatch.setattr(vt.urllib.request, "urlopen", boom)
    for name in ("POSTHOG_PERSONAL_API_KEY", "POSTHOG_PROJECT_ID"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(vt, "get_secret", lambda *n: (None, None))
    p = plan(tmp_path, event("page_view"))
    for source in ("ga4", "posthog"):
        out = vt.verify(p, source, store=tmp_path / "s.json")
        assert out["connection"]["status"] == "unconnected" and out["connection"]["owner_steps"]
        assert out["verdict"] == "not_ready"


def test_export_preset_rejects_missing_columns_and_stays_aggregate(tmp_path):
    import pytest
    p = plan(tmp_path, event("page_view"))
    with pytest.raises(ValueError):
        vt.verify(p, "ga4", export=export(tmp_path, ["page_view,1"], header="Name,Hits"), metadata=META)
    with pytest.raises(ValueError):
        vt.verify(p, "ga4", export=export(tmp_path, ["a@example.test,1"]), metadata=META)


def test_consent_gated_zero_is_unknown_not_not_observed(tmp_path):
    p = plan(tmp_path, event("page_view"),
             event("ad_click", consent_category="marketing", consent_gated=True),
             event("newsletter", consent_category="marketing", consent_gated=False))
    out = vt.verify(p, "ga4", export=export(tmp_path, ["page_view,50", "ad_click,0"]), metadata=META)
    by = {e["name"]: e for e in out["events"]}
    assert by["ad_click"]["status"] == "unknown_consent_gated"
    assert by["newsletter"]["status"] == "not_observed"
    assert out["verdict"] == "not_ready"


def test_export_properties_are_unverifiable_and_short_period_blocks(tmp_path):
    p = plan(tmp_path, event("generate_lead", required_properties=["form_id"]))
    out = vt.verify(p, "ga4", export=export(tmp_path, ["generate_lead,5"]), metadata=META)
    assert out["events"][0]["properties"]["form_id"] == "unknown" and out["verdict"] == "not_ready"
    p2 = plan(tmp_path, event("page_view"))
    short = META | {"period_start": "2026-10-29"}
    out = vt.verify(p2, "ga4", export=export(tmp_path, ["page_view,5"]), metadata=short)
    assert out["verdict"] == "not_ready" and any("period" in r for r in out["reasons"])


def test_output_has_no_secrets_or_row_data(tmp_path):
    out = vt.verify(plan(tmp_path, event("page_view")), "ga4", export=export(tmp_path, ["page_view,3"]), metadata=META)
    text = json.dumps(out)
    assert "Bearer" not in text and "@" not in text
