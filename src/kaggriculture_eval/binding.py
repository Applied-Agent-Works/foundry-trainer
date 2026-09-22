"""Explicit, content-addressed binding to the Kaggriculture system under test."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET_ROOT = PROJECT_ROOT.parent / "kaggriculture"


@dataclass(frozen=True)
class TargetBinding:
    root: Path
    shared_path: Path
    engine_path: Path
    revision: str
    shared_sha256: str
    engine_sha256: str
    shared: ModuleType


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def bind_target(target_root: str | Path | None = None) -> TargetBinding:
    """Load the target shared policy without an ambiguous ``agents`` import."""
    configured = target_root or os.environ.get("KAGGRICULTURE_TARGET_ROOT") or DEFAULT_TARGET_ROOT
    root = Path(configured).expanduser().resolve()
    shared_path = root / "agents" / "carrot" / "shared.py"
    engine_path = root / "kaggriculture.py"
    if not root.is_absolute() or not shared_path.is_file() or not engine_path.is_file():
        raise RuntimeError(
            "Kaggriculture target binding requires an absolute directory containing "
            "agents/carrot/shared.py and kaggriculture.py; set KAGGRICULTURE_TARGET_ROOT."
        )
    # ``make("kaggriculture")`` resolves this explicitly supplied target game
    # module.  It does not make target policy imports implicit.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    shared_hash = _sha256(shared_path)
    module_name = f"kaggriculture_eval_target_shared_{shared_hash[:16]}"
    module = sys.modules.get(module_name)
    if module is None:
        spec = importlib.util.spec_from_file_location(module_name, shared_path)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load target policy source: {shared_path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    return TargetBinding(root, shared_path, engine_path, _revision(root), shared_hash, _sha256(engine_path), module)
