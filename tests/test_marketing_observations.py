import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("marketing_observations", ROOT / "scripts/marketing/observations.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def test_export_keeps_unknown_separate_from_zero_and_drops_private_columns(tmp_path):
    source = tmp_path / "export.csv"
    source.write_text("property,source,start,end,tz,page,metric,unit,value,email\nsite,gsc,2026-01-01,2026-01-07,UTC,/,clicks,count,0,a@example.test\nsite,gsc,2026-01-08,2026-01-14,UTC,/,clicks,count,,b@example.test\n")
    mapping = {"property":"property", "source":"source", "period_start":"start", "period_end":"end", "timezone":"tz", "page":"page", "metric":"metric", "unit":"unit", "value":"value"}
    out = module.normalize(source, mapping, {"exported_at":"2026-02-01"})
    assert out["observations"][0]["value"] == 0
    assert out["observations"][1]["availability"] == "unknown"
    assert "email" not in json.dumps(out)


def test_rejects_identifiers_and_incomplete_or_noncomparable_metadata(tmp_path):
    source = tmp_path / "e.json"
    source.write_text(json.dumps([{"p":"site", "s":"gsc", "b":"2026-01-01", "e":"2026-01-02", "tz":"UTC", "m":"clicks", "u":"count", "v":2, "email":"x"}]))
    required = {"property":"p", "source":"s", "period_start":"b", "period_end":"e", "timezone":"tz", "metric":"m", "unit":"u", "value":"v"}
    with pytest.raises(ValueError): module.normalize(source, required | {"email":"email"}, {})
    out = module.normalize(source, required, {"exported_at":"2026-02-01"})
    assert "email" not in json.dumps(out)
    with pytest.raises(ValueError): module.normalize(source, {"property":"p"}, {})


def test_comparison_requires_like_for_like_window_and_preserves_denominators(tmp_path):
    source = tmp_path / "series.csv"
    source.write_text("property,source,start,end,tz,page,metric,unit,value,denom\nsite,gsc,2026-01-01,2026-01-07,UTC,/,leads,count,2,40\n")
    mapping = {"property":"property", "source":"source", "period_start":"start", "period_end":"end", "timezone":"tz", "page":"page", "metric":"metric", "unit":"unit", "value":"value", "denominator":"denom"}
    before = module.normalize(source, mapping, {"exported_at":"2026-01-08"})
    source.write_text(source.read_text().replace("2026-01-01,2026-01-07", "2026-01-08,2026-01-14").replace(",2,40", ",3,50"))
    after = module.normalize(source, mapping, {"exported_at":"2026-01-15"})
    row = module.compare(before, after)["results"][0]
    assert row["status"] == "observed_change" and row["difference"] == 1
    assert row["before_denominator"] == 40 and row["causal_attribution"] == "not_established"
    source.write_text(source.read_text().replace("2026-01-08,2026-01-14", "2026-01-08,2026-01-20"))
    mismatch = module.normalize(source, mapping, {"exported_at":"2026-01-21"})
    assert module.compare(before, mismatch)["results"][0]["status"] == "non_comparable"


def test_unavailable_export_value_is_never_treated_as_zero(tmp_path):
    source = tmp_path / "unavailable.json"
    source.write_text(json.dumps([{"p":"site", "s":"gsc", "b":"2026-01-01", "e":"2026-01-07", "tz":"UTC", "m":"clicks", "u":"count", "v":"", "a":"suppressed"}]))
    mapping = {"property":"p", "source":"s", "period_start":"b", "period_end":"e", "timezone":"tz", "metric":"m", "unit":"u", "value":"v", "availability":"a"}
    out = module.normalize(source, mapping, {"exported_at":"2026-02-01"})
    assert out["observations"][0]["availability"] == "unavailable"
    assert out["observations"][0]["value"] is None


def test_synthetic_export_to_change_to_decision_example_and_stale_binding():
    fixture = ROOT / "fixtures/marketing"
    mapping = json.loads((fixture / "demo-mapping.json").read_text())
    baseline = module.normalize(fixture / "demo-baseline.csv", mapping, {"exported_at":"2026-01-08"})
    followup = module.normalize(fixture / "demo-followup.csv", mapping, {"exported_at":"2026-01-15"})
    record = module.decision_record(action_id="stellar-demo-conversion", before=baseline, after=followup,
        changed_at="2026-01-07", expected_effect="Make a service request path usable end to end",
        applied_change="Replace inert CTA with validated local demo form", confounders=["synthetic fixture data"],
        limitations=["No customer visit, lead, or production analytics"], next_decision="collect_more_data")
    expected = json.loads((fixture / "demo-decision.json").read_text())
    assert record == expected
    assert record["action_id"] == "stellar-demo-conversion"
    assert record["comparison"]["results"][0]["difference"] == 1
    assert record["causal_claim"] == "not_established"
    assert module.decision_record_is_current(record, baseline, followup)
    followup["input_sha256"] = "0" * 64
    assert not module.decision_record_is_current(record, baseline, followup)


def test_decision_record_rejects_followup_that_overlaps_the_change(tmp_path):
    source = tmp_path / "overlap.csv"
    source.write_text("property,source,start,end,tz,metric,unit,value\nsite,gsc,2026-01-07,2026-01-13,UTC,clicks,count,1\n")
    mapping = {"property":"property", "source":"source", "period_start":"start", "period_end":"end", "timezone":"tz", "metric":"metric", "unit":"unit", "value":"value"}
    report = module.normalize(source, mapping, {"exported_at":"2026-01-14"})
    with pytest.raises(ValueError):
        module.decision_record(action_id="a", before=report, after=report, changed_at="2026-01-07",
            expected_effect="effect", applied_change="change", confounders=[], limitations=[], next_decision="continue")
