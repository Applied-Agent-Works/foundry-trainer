#!/usr/bin/env python3
"""Trace all registered graph proposals over shared baseline observations."""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kaggriculture_eval.binding import TargetBinding  # noqa: E402
from kaggriculture_eval.graph_registry import bind_registered_graphs, graph_descriptors  # noqa: E402
from kaggriculture_eval.shadow import trace_shadow_observations  # noqa: E402


def _read_cache(path: Path) -> dict[str, Any]:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict) or not isinstance(value.get("turns"), list):
        raise ValueError(f"baseline cache has no readable turns list: {path}")
    return value


def _observations(cache_files: list[Path], stride: int, max_turns: int | None) -> list[tuple[int, int, int, dict[str, Any]]]:
    if stride < 1:
        raise ValueError("stride must be at least 1")
    rows: list[tuple[int, int, int, dict[str, Any]]] = []
    for path in cache_files:
        cache = _read_cache(path)
        match = cache["match"]
        turns = cache["turns"][:max_turns] if max_turns is not None else cache["turns"]
        for turn in turns[::stride]:
            rows.append((int(match["seed"]), int(match["decision_player"]), int(turn["turn"]), turn["observation"]))
    return rows


def _json_observations(paths: list[Path]) -> list[tuple[int, int, int, dict[str, Any]]]:
    rows: list[tuple[int, int, int, dict[str, Any]]] = []
    for path in paths:
        values = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(values, list):
            raise ValueError(f"observation fixture must contain a JSON list: {path}")
        for index, item in enumerate(values):
            if not isinstance(item, dict) or not isinstance(item.get("observation"), dict):
                raise ValueError(f"observation fixture item {index} is malformed: {path}")
            rows.append((int(item.get("seed", 0)), int(item.get("seat", 0)), int(item.get("turn", index)), item["observation"]))
    return rows


def _write_exclusive(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with path.open("xb") as stream:
        stream.write(encoded)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-root", type=Path, required=True)
    parser.add_argument("--cache-file", type=Path, action="append")
    parser.add_argument("--observation-json", type=Path, action="append")
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--max-turns", type=int)
    args = parser.parse_args()

    if not args.cache_file and not args.observation_json:
        parser.error("provide at least one --cache-file or --observation-json")
    if args.cache_file and args.observation_json:
        parser.error("do not mix --cache-file and --observation-json")
    bindings = bind_registered_graphs(args.target_root)
    observations = (
        _observations(args.cache_file or [], args.stride, args.max_turns)
        if args.cache_file
        else _json_observations(args.observation_json or [])
    )
    rows = trace_shadow_observations(observations, bindings)
    report = {
        "schema_version": 1,
        "kind": "local-shadow-trace-v1",
        "target_revision": next(iter(bindings.values())).revision,
        "source_cache_files": [str(path) for path in (args.cache_file or [])],
        "source_observation_files": [str(path) for path in (args.observation_json or [])],
        "source_observation_kind": "baseline-cache" if args.cache_file else "synthetic-diagnostic-fixture",
        "stride": args.stride,
        "graph_ids": [descriptor.graph_id for descriptor in graph_descriptors()],
        "graph_lifecycles": {descriptor.graph_id: descriptor.lifecycle for descriptor in graph_descriptors()},
        "observation_count": len(rows),
        "disagreement_count": sum(row["disagreement"] for row in rows),
        "investment_disagreement_count": sum(row["investment_disagreement"] for row in rows),
        "proposals_are_not_applied": True,
        "foundry_packet_written": False,
        "records": rows,
    }
    destination = args.report_dir / "shadow-trace-v1.json"
    _write_exclusive(destination, report)
    print(json.dumps({
        "report_path": str(destination),
        "target_revision": report["target_revision"],
        "graph_count": len(report["graph_ids"]),
        "observation_count": report["observation_count"],
        "disagreement_count": report["disagreement_count"],
        "investment_disagreement_count": report["investment_disagreement_count"],
        "proposals_are_not_applied": report["proposals_are_not_applied"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
