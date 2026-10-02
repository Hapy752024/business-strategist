import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("research_yield", ROOT / "scripts/evidence_scout/build_research_yield.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


def test_plan_cells_survive_zero_records_and_execution_failures():
    plan = {"input_plan": {"queries": [
        {"query_id":"q1", "cell_id":"a", "locale":"DE:de", "source_family":"reddit"},
        {"query_id":"q2", "cell_id":"b", "locale":"FR:fr", "source_family":"youtube"}]}}
    out = module.build(plan, [], [], [{"query_id":"q1", "status":"returned_zero"}, {"query_id":"q2", "status":"access_failed"}])
    cells = {row["cell_id"]: row for row in out["cells"]}
    assert cells["a"]["cell_status"] == "returned_zero"
    assert cells["b"]["cell_status"] == "access_failed"


def test_missing_execution_ledger_is_unknown_not_zero():
    plan = {"input_plan": {"queries": [{"query_id":"q1", "cell_id":"a"}]}}
    assert module.build(plan, [], [])["cells"][0]["cell_status"] == "execution_unknown"
    assert module.build(plan, [], [], [])["cells"][0]["cell_status"] == "not_attempted"
