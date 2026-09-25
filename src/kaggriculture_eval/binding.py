"""Crop-neutral, content-addressed binding to a Kaggriculture target."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any

from .adapters import PolicyAdapter


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET_ROOT = PROJECT_ROOT.parent / "kaggriculture"


@dataclass(frozen=True)
class TargetBinding:
    """A target checkout plus the explicit adapter that describes its policy."""

    root: Path
    shared_path: Path
    engine_path: Path
    revision: str
    shared_sha256: str
    engine_sha256: str
    shared: ModuleType
    adapter: PolicyAdapter
    parameter_module: ModuleType
    source_hashes: dict[str, str]

    @property
    def parameter_type(self) -> Any:
        return getattr(self.parameter_module, self.adapter.parameter_type_attribute)

    @property
    def default_parameters(self) -> Any:
        return getattr(self.parameter_module, self.adapter.default_parameters_attribute)

    @property
    def policy_id(self) -> str:
        return self.adapter.policy_id

    @property
    def opponent_id(self) -> str:
        return self.adapter.opponent_id

    def decision_agent(self, observation: dict, parameters: Any | None = None) -> dict:
        """Invoke the adapter's policy using an optional in-memory override."""
        if self.adapter.decision_mode == "wrapper":
            policy = getattr(self.shared, self.adapter.policy_attribute)
            return policy(observation) if parameters is None else policy(observation, parameters)
        if self.adapter.decision_mode == "helper":
            helper = getattr(self.parameter_module, "decision_agent")
            crop = getattr(self.shared, self.adapter.crop_constant_attribute or "")
            return helper(observation, crop, parameters or self.default_parameters)
        raise RuntimeError(f"unsupported decision adapter mode: {self.adapter.decision_mode}")

    def opponent_agent(self, observation: dict) -> dict:
        """Invoke the adapter's deterministic comparison opponent."""
        if self.adapter.opponent_mode == "wrapper":
            return getattr(self.shared, self.adapter.opponent_attribute)(observation)
        if self.adapter.opponent_mode == "helper":
            helper = getattr(self.parameter_module, "conveyor_agent")
            crop = getattr(self.shared, self.adapter.crop_constant_attribute or "")
            return helper(observation, crop)
        raise RuntimeError(f"unsupported opponent adapter mode: {self.adapter.opponent_mode}")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _load_module(path: Path, module_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load target source: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def bind_target(
    target_root: str | Path | None = None, *, adapter: PolicyAdapter
) -> TargetBinding:
    """Bind an explicitly supplied checkout through an explicit adapter.

    There is intentionally no default crop. Callers must select the adapter
    whose policy, opponent, and parameter paths they reviewed.
    """
    configured = target_root or os.environ.get("KAGGRICULTURE_TARGET_ROOT") or DEFAULT_TARGET_ROOT
    root = Path(configured).expanduser().resolve()
    shared_path = root / adapter.shared_relative_path
    engine_path = root / "kaggriculture.py"
    parameter_relative_path = adapter.parameter_relative_path or adapter.shared_relative_path
    parameter_path = root / parameter_relative_path
    if not root.is_absolute() or not shared_path.is_file() or not engine_path.is_file() or not parameter_path.is_file():
        raise RuntimeError(
            "Kaggriculture target binding requires an absolute checkout with "
            f"{adapter.shared_relative_path}, {parameter_relative_path}, and kaggriculture.py."
        )
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    source_paths = {
        "kaggriculture.py": engine_path,
        adapter.shared_relative_path: shared_path,
        parameter_relative_path: parameter_path,
    }
    source_hashes = {name: _sha256(path) for name, path in source_paths.items()}
    shared = _load_module(
        shared_path,
        f"kaggriculture_eval_target_shared_{source_hashes[adapter.shared_relative_path][:16]}",
    )
    if parameter_path == shared_path:
        parameter_module = shared
    else:
        parameter_module = _load_module(
            parameter_path,
            f"kaggriculture_eval_target_parameters_{source_hashes[parameter_relative_path][:16]}",
        )

    return TargetBinding(
        root=root,
        shared_path=shared_path,
        engine_path=engine_path,
        revision=_revision(root),
        shared_sha256=source_hashes[adapter.shared_relative_path],
        engine_sha256=source_hashes["kaggriculture.py"],
        shared=shared,
        adapter=adapter,
        parameter_module=parameter_module,
        source_hashes=source_hashes,
    )
