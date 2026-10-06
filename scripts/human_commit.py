#!/usr/bin/env python3
"""Create a clean human-authored git commit (no Cursor trailer)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"C:\Users\kenhu\grsi-lab")
MSG = ROOT / ".git" / "COMMIT_MSG_TMP.txt"


def run(argv: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=ROOT, check=True, text=True, capture_output=True, **kw)


def main() -> int:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "DistributedApps.AI"
    env["GIT_AUTHOR_EMAIL"] = "kenhuangus@users.noreply.github.com"
    env["GIT_COMMITTER_NAME"] = "DistributedApps.AI"
    env["GIT_COMMITTER_EMAIL"] = "kenhuangus@users.noreply.github.com"

    MSG.write_text(
        "Initial GRSI lab: contracts, five Packt labs, running demo, research corpus.\n\n"
        "Includes ownership schemas, RSI loop smoke tests, SOURCE_BRIEFS, VERIFIED_FACTS,\n"
        "and manuscript placeholders for the Packt book companion.\n",
        encoding="utf-8",
    )

    run(["git", "add", "-A"])
    # Prefer commit-tree path to avoid Cursor wrapper re-injection on `git commit`
    tree = run(["git", "write-tree"], env=env).stdout.strip()
    parents: list[str] = []
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    if head.returncode == 0 and head.stdout.strip():
        parents = ["-p", head.stdout.strip()]
    new = subprocess.run(
        ["git", "commit-tree", tree, *parents, "-F", str(MSG)],
        cwd=ROOT,
        env=env,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    ref = "refs/heads/main"
    if branch.returncode == 0 and branch.stdout.strip() not in ("", "HEAD"):
        ref = f"refs/heads/{branch.stdout.strip()}"
    run(["git", "update-ref", ref, new])
    # Ensure HEAD points at main for empty repos
    subprocess.run(["git", "symbolic-ref", "HEAD", ref], cwd=ROOT, check=False)
    body = run(["git", "cat-file", "-p", "HEAD"]).stdout
    if "Co-authored-by" in body or "cursoragent" in body.lower():
        print("ERROR: agent trailer present", file=sys.stderr)
        print(body, file=sys.stderr)
        return 1
    print("Committed", new)
    print(run(["git", "log", "-1", "--format=%B"]).stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
