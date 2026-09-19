"""Check frozen source-fixture integrity, not semantic model performance."""
import json
from collections import Counter
from pathlib import Path


def main():
    root = Path(__file__).parent
    data = json.loads((root / "cases.json").read_text())
    sources = {s["id"]: s for s in data["sources"]}
    studies = {s["id"] for s in data["studies"]}
    cases = data["cases"]
    assert len({c["id"] for c in cases}) == len(cases)
    quote_words = Counter()
    for case in cases:
        assert case["source_id"] in sources
        assert case["study_id"] in studies
        assert case["quote"] and case["source_locator"] and case["must_not_conclude"]
        assert case["expected_voice"] in {"customer", "supplier"}
        quote_words[case["source_id"]] += len(case["quote"].split())
        if case["expected_voice"] == "supplier":
            assert not case["expected_concepts"]["needs"]
            assert not case["expected_concepts"]["requirements"]
    assert all(n <= 25 for n in quote_words.values()), quote_words
    raw = json.loads((root / "raw/firecrawl-topic-search.json").read_text())
    assert raw["success"] is True
    result = next(p for p in raw["data"]["web"] if p["url"] == sources["S1"]["url"])
    assert cases[0]["quote"] in result["markdown"]
    print(json.dumps({
        "integrity": "pass",
        "studies": len(studies),
        "semantic_exercises": len(cases),
        "source_pages": len(sources),
        "languages": sorted({s["original_language"] for s in sources.values()}),
        "supplier_controls": sum(c["expected_voice"] == "supplier" for c in cases),
        "human_gold": False,
        "held_out": False,
        "semantic_model_comparison_executed": False,
    }, indent=2))


if __name__ == "__main__":
    main()
