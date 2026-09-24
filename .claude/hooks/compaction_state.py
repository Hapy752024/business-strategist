"""Session-scoped checkpoint helpers shared by compaction lifecycle hooks."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any


def project_root() -> Path:
    configured = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(configured).resolve() if configured else Path(__file__).resolve().parents[2]


def resume_path(root: Path, session_id: str) -> Path:
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("Claude session_id is required for a session-scoped resume file")
    # Do not let a host-supplied session ID escape the resume directory.
    safe_id = session_id if re.fullmatch(r"[A-Za-z0-9._-]{1,128}", session_id) else hashlib.sha256(session_id.encode()).hexdigest()
    return root / ".claude" / "plans" / "resume" / f"{safe_id}.json"


def write_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def load_state(path: Path, session_id: str) -> dict[str, Any] | None:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return state if state.get("session_id") == session_id else None


def active_workspace(root: Path, hook_cwd: str | None, *, selected_project: str | None = None,
                     selected_module: str | None = None, selected_case: str | None = None,
                     selected_run: str | None = None) -> dict[str, Any] | None:
    if not isinstance(hook_cwd, str) or not hook_cwd:
        return None
    cwd = Path(hook_cwd).resolve()
    if selected_project:
        slug = Path(selected_project).name
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            return None
        project = (root / "projects" / slug).resolve()
        if not project.is_relative_to((root / "projects").resolve()):
            return None
        rel = project.relative_to(root) / (selected_module or "")
    else:
        if not cwd.is_relative_to(root):
            return None
        rel = cwd.relative_to(root)
        if len(rel.parts) < 2 or rel.parts[0] != "projects":
            return None
        slug = rel.parts[1]
    project = root / "projects" / slug
    if not project.is_dir():
        return None

    case_id = None
    run_id = None
    if selected_case:
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", selected_case):
            return None
        case_id = selected_case
    elif "cases" in rel.parts:
        index = rel.parts.index("cases")
        if index + 1 < len(rel.parts):
            case_id = rel.parts[index + 1]
    if selected_run:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", selected_run):
            return None
        run_id = selected_run
    elif "runs" in rel.parts:
        index = rel.parts.index("runs")
        if index + 1 < len(rel.parts):
            run_id = rel.parts[index + 1]

    module = selected_module
    if not module and "branding" in rel.parts:
        module = "branding"
    elif not module and "marketing" in rel.parts:
        module = "marketing"
    elif not module and ("website" in rel.parts or "web-site" in rel.parts):
        module = "website"
    elif not module and ("business-analysis" in rel.parts or "business" in rel.parts):
        module = "business"

    project_state: dict[str, Any] = {}
    try:
        project_state = json.loads((project / "project-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    subprojects = project_state.get("subprojects", {}) if isinstance(project_state, dict) else {}
    if module is None and isinstance(subprojects, dict):
        for name, entry in subprojects.items():
            registered = entry.get("path") if isinstance(entry, dict) else None
            if registered:
                candidate = (project / registered).resolve()
                if cwd.is_relative_to(candidate):
                    module = name
                    break
    module = {"research": "business", "venture_strategy": "business"}.get(module, module)
    module_name = module or "business"
    default_paths = {"business": "business-analysis", "branding": "branding", "marketing": "marketing",
                     "website": "digital-assets/website", "others": "digital-assets/others"}
    module_path = (subprojects.get(module_name, {}).get("path") if isinstance(subprojects, dict) else None) or default_paths.get(module_name, "")
    module_root = project / module_path if module_path else project
    if not module_root.resolve().is_relative_to(project.resolve()):
        return None
    if case_id and module_name == "business":
        case_roots = [module_root / "cases" / case_id, project / "business" / "cases" / case_id,
                      project / "cases" / case_id]
        case_root = next((p for p in case_roots if p.is_dir()), case_roots[0])
        manifest_candidates = [case_root / "market_research" / "manifest.json"]
    elif module_name == "marketing":
        manifest_candidates = [module_root / "workstream.json", project / "project-manifest.json"]
    elif module_name in {"branding", "website", "others"}:
        manifest_candidates = [module_root / "brief.md", project / "project-manifest.json"]
    else:
        manifest_candidates = [module_root / "market_research" / "manifest.json",
                               project / "business" / "market_research" / "manifest.json",
                               project / "market_research" / "manifest.json"]
    if not case_id and module_name == "business":
        manifest_candidates.append(project / "project-manifest.json")
    manifest_path = next((p for p in manifest_candidates if p.is_file()), None)
    manifest: dict[str, Any] = {}
    manifest_digest = None
    if manifest_path:
        try:
            content = manifest_path.read_bytes()
            manifest = json.loads(content)
            manifest_digest = hashlib.sha256(content).hexdigest()
        except (OSError, json.JSONDecodeError):
            manifest = {}
    run_manifest = None
    if run_id:
        run_parents = [case_root / "market_research" if case_id and module_name == "business" else module_root / "market_research",
                       module_root, project / "market_research"]
        candidates = [parent / "pain_points" / "runs" / run_id / "run-manifest.json" for parent in run_parents]
        run_path = next((candidate for candidate in candidates if candidate.is_file()), None)
        if run_path:
            run_manifest = run_path.relative_to(root).as_posix()

    return {
        "project_slug": slug,
        "project_path": project.relative_to(root).as_posix(),
        "module": module,
        "case_id": case_id,
        "run_id": run_id,
        "manifest_path": manifest_path.relative_to(root).as_posix() if manifest_path else None,
        "manifest_sha256": manifest_digest,
        "current_stage": manifest.get("current_stage", "unknown"),
        "updated_at": manifest.get("updated_at", ""),
        "next_action": manifest.get("next_action", ""),
        "open_blockers": manifest.get("open_blockers", []),
        "run_manifest_path": run_manifest,
        "open_question": "",
        "accepted_decisions": [],
    }
