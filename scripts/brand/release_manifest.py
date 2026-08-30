#!/usr/bin/env python3
"""Record GitHub/Vercel release state without deploying or changing traffic."""

from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


COMMIT_RE = re.compile(r"^[a-f0-9]{7,40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")


def write_atomic(path: Path, data: dict, *, expected_revision: int) -> None:
    current = json.loads(path.read_text(encoding="utf-8"))
    actual_revision = int(current.get("manifest_revision", 1))
    if actual_revision != expected_revision:
        raise RuntimeError(f"manifest revision conflict: expected {expected_revision}, found {actual_revision}")
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        temporary.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def valid_https(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password and not parsed.query and not parsed.fragment


def update(path: Path, *, status: str, commit: str, url: str = "", rollback_commit: str = "", confirm_production: bool = False, github_repo: str = "", github_branch: str = "", vercel_project: str = "") -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    expected_revision = int(data.get("manifest_revision", 1))
    if not COMMIT_RE.fullmatch(commit):
        raise ValueError("commit must be a 7-40 character lowercase Git SHA")
    if status in {"preview", "production"} and not valid_https(url):
        raise ValueError(f"{status} status requires a credential-free HTTPS URL")
    if rollback_commit and not COMMIT_RE.fullmatch(rollback_commit):
        raise ValueError("rollback commit must be a 7-40 character lowercase Git SHA")
    if status == "rolled_back" and not rollback_commit:
        raise ValueError("rolled_back status requires rollback_commit")
    qa = data.get("qa", {})
    if status == "preview" and qa.get("build") != "pass":
        raise ValueError("Preview recording requires a passing build gate")
    if status == "production":
        if not confirm_production:
            raise ValueError("production status requires explicit confirmation")
        incomplete = sorted(key for key in ("build", "accessibility", "performance", "responsive", "visual_review") if qa.get(key) != "pass")
        if incomplete:
            raise ValueError(f"production release has incomplete QA gates: {', '.join(incomplete)}")
    release = data.setdefault("release", {})
    resolved_repo = github_repo or str(release.get("github_repo", ""))
    resolved_branch = github_branch or str(release.get("github_branch", ""))
    resolved_vercel = vercel_project or str(release.get("vercel_project", ""))
    if resolved_repo and not REPO_RE.fullmatch(resolved_repo):
        raise ValueError("GitHub repository must use owner/repository form")
    if resolved_branch and (not NAME_RE.fullmatch(resolved_branch) or ".." in resolved_branch):
        raise ValueError("invalid GitHub branch name")
    if resolved_vercel and (not NAME_RE.fullmatch(resolved_vercel) or "/" in resolved_vercel):
        raise ValueError("invalid Vercel project name")
    if status == "production" and not all((resolved_repo, resolved_branch, resolved_vercel)):
        raise ValueError("production record requires GitHub repo/branch and Vercel project")
    release["status"] = status
    release["environment"] = "production" if status == "production" else "preview" if status == "preview" else release.get("environment", "production")
    release["commit"] = commit
    release["recorded_at"] = datetime.now(timezone.utc).isoformat()
    for key, value in (("github_repo", resolved_repo), ("github_branch", resolved_branch), ("vercel_project", resolved_vercel)):
        if value:
            release[key] = value
    if url:
        release["preview_url" if status == "preview" else "production_url"] = url
    if rollback_commit:
        release["rollback_commit"] = rollback_commit
    data["manifest_revision"] = expected_revision + 1
    data["updated_at"] = datetime.now(timezone.utc).isoformat()
    write_atomic(path, data, expected_revision=expected_revision)
    return release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--status", choices=("preview", "production", "rolled_back"), required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--url", default="")
    parser.add_argument("--rollback-commit", default="")
    parser.add_argument("--confirm-production", action="store_true")
    parser.add_argument("--github-repo", default="")
    parser.add_argument("--github-branch", default="")
    parser.add_argument("--vercel-project", default="")
    args = parser.parse_args()
    try:
        release = update(args.manifest, status=args.status, commit=args.commit, url=args.url, rollback_commit=args.rollback_commit, confirm_production=args.confirm_production, github_repo=args.github_repo, github_branch=args.github_branch, vercel_project=args.vercel_project)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps({"status": "recorded", "release": release}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
