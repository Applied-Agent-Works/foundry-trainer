"""Builders for deliberately constructed, non-simulator shadow observations."""

from __future__ import annotations

from typing import Any


def build_observation(scenario: dict[str, Any]) -> dict[str, Any]:
    """Expand one compact selector scenario into a policy-shaped observation."""
    tiles = scenario.get("tiles", [[None]])
    farm = {"money": scenario.get("money", 3000), "farmer": [0, 0], "tiles": tiles}
    other_farm = {"money": 3000, "farmer": [0, 0], "tiles": [[None]]}
    return {
        "day": scenario.get("day", 0),
        "player": 0,
        "farms": [farm, other_farm],
        "private": {"seeds": scenario.get("seeds", {}), "shed": {}},
        "market": {"prices": scenario["prices"]},
        "town": {"unlocked_shops": []},
    }
