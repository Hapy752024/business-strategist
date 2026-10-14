#!/usr/bin/env python3
"""Local agent evaluation entrypoint; no central service dependency."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))
from local_evaluation import main
CONFIG = {'project': 'business-strategist', 'checks': [['python3', 'scripts/run_evals.py'], ['python3', 'scripts/run_behavioral_evals.py', '--repeat', '3'], ['python3', 'scripts/run_analysis_evals.py', '--validate-only'], ['python3', 'evals/test_local_evaluation.py']], 'full_checks': [['bash', 'scripts/validate_setup.sh']]}
if __name__ == "__main__":
    raise SystemExit(main(ROOT, CONFIG))
