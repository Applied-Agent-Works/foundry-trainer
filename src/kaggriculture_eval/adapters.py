"""Declarative target adapters used by the crop-neutral evaluator.

The evaluator core knows only how to load the paths and invoke the operations
described here. Crop names, entry-point names, and parameter locations live in
this adapter layer so the binding base has no preferred crop.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyAdapter:
    """Describe one target policy without embedding it in evaluator logic."""

    adapter_id: str
    shared_relative_path: str
    policy_id: str
    opponent_id: str
    policy_attribute: str
    opponent_attribute: str
    parameter_relative_path: str | None
    parameter_type_attribute: str
    default_parameters_attribute: str
    decision_mode: str
    opponent_mode: str
    crop_constant_attribute: str | None = None

