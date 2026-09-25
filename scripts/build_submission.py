#!/usr/bin/env python3
"""Build the current Carrot submission without executing the simulator.

The notebooks are design/evidence artifacts. This command packages only the
promoted Python boundaries and the fixture-backed Blazor demonstration.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CARROT_ROOT = ROOT / "carrot-tuning-system"
DIST = ROOT / "submission" / "dist"
WEB_OUT = DIST / "web"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str) -> None:
    print("+", " ".join(args))
    subprocess.run(args, cwd=ROOT, check=True)


def validate_python_surface() -> None:
    sources = [CARROT_ROOT / "analyst", CARROT_ROOT / "evaluator"]
    run(sys.executable, "-m", "compileall", "-q", *(str(path) for path in sources))
    sys.path.insert(0, str(CARROT_ROOT))
    from analyst import (  # noqa: PLC0415
        EvidenceCitation,
        validate_analyst_response,
    )

    brief_payload = json.loads(
        (ROOT / "submission/fixtures/evidence_brief.json").read_text(encoding="utf-8")
    )
    response = json.loads(
        (ROOT / "submission/fixtures/evidence_analyst_response.json").read_text(
            encoding="utf-8"
        )
    )
    # The package-level smoke check exercises the response gate directly. The
    # full packet gate remains covered by the existing simulator-free tests.
    allowed = [EvidenceCitation(**item) for item in brief_payload["citations"]]
    validate_analyst_response(
        response,
        packet_sha256=brief_payload["packet_sha256"],
        allowed_citations=allowed,
        required_limitations=brief_payload["limitations"],
    )
    print("Python source and redacted response gate: PASS")


def copy_runtime_sources() -> list[str]:
    runtime = DIST / "python"
    if runtime.exists():
        shutil.rmtree(runtime)
    copied: list[str] = []
    for package in ("analyst", "evaluator"):
        source = CARROT_ROOT / package
        destination = runtime / package
        shutil.copytree(source, destination, ignore=shutil.ignore_patterns("__pycache__"))
        copied.extend(str(path.relative_to(ROOT)) for path in destination.rglob("*.py"))
    return sorted(copied)


def main() -> int:
    DIST.mkdir(parents=True, exist_ok=True)
    validate_python_surface()
    run("dotnet", "publish", str(ROOT / "submission/demo/demo.csproj"), "-c", "Release", "-o", str(WEB_OUT), "--nologo")
    copied = copy_runtime_sources()
    fixture_paths = sorted((ROOT / "submission/fixtures").glob("*.json"))
    manifest = {
        "package_version": 1,
        "agents": [
            {"name": "evidence-analyst", "version": "2", "status": "complete"},
            {"name": "evidence-analyst-judge", "version": "1", "status": "complete"},
            {"name": "experiment-proposal-drafter", "version": "3", "status": "complete"},
        ],
        "source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "python_sources": copied,
        "fixtures": {
            str(path.relative_to(ROOT)): sha256(path) for path in fixture_paths
        },
        "web_publish_directory": str(WEB_OUT.relative_to(ROOT)),
        "notebooks_in_runtime": False,
        "cloud_actions_performed": False,
        "commands": ["compileall analyst evaluator", "dotnet publish demo.csproj"],
    }
    (DIST / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Submission built: {DIST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
