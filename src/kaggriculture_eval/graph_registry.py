"""The local catalogue of decision graphs that can participate in shadow mode.

The registry is deliberately descriptive.  It does not choose an action or
combine crop policies; it gives the local evaluator one stable vocabulary for
binding and inspecting the standalone graphs.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .adapters import PolicyAdapter
from .binding import TargetBinding, bind_target
from .carrot_adapter import CARROT_ADAPTER
from .melon_adapter import MELON_ADAPTER
from .strawberry_adapter import STRAWBERRY_ADAPTER
from .tomato_adapter import TOMATO_ADAPTER
from .wheat_adapter import WHEAT_ADAPTER

if TYPE_CHECKING:
    from os import PathLike


@dataclass(frozen=True)
class DecisionGraphDescriptor:
    """Stable metadata for one standalone decision graph."""

    graph_id: str
    display_name: str
    crop: str
    lifecycle: str
    parameter_namespace: str
    seed_cost: int
    planning_horizon: int
    adapter: PolicyAdapter
    supported_actions: tuple[str, ...]
    supported_stages: tuple[str, ...]
    limitations: tuple[str, ...]


_COMMON_STAGES = ("plan", "baseline", "candidate", "divergence", "audit")
_ONE_TIME_ACTIONS = ("PLANT", "PASS", "WATER", "HARVEST", "MOVE", "BUY_SEED", "SELL")


GRAPH_REGISTRY: dict[str, DecisionGraphDescriptor] = {
    "carrot_investment": DecisionGraphDescriptor(
        graph_id="carrot_investment",
        display_name="Carrot investment",
        crop="CARROT",
        lifecycle="one-time-crop",
        parameter_namespace="CarrotParameters",
        seed_cost=20,
        planning_horizon=2,
        adapter=CARROT_ADAPTER,
        supported_actions=_ONE_TIME_ACTIONS,
        supported_stages=_COMMON_STAGES,
        limitations=(
            "carrot-only economic branch",
            "does not select among crops",
            "does not model shared land, labor, or feed capacity",
        ),
    ),
    "wheat_crop": DecisionGraphDescriptor(
        graph_id="wheat_crop",
        display_name="Wheat crop",
        crop="WHEAT",
        lifecycle="one-time-crop",
        parameter_namespace="PointPriceParameters",
        seed_cost=10,
        planning_horizon=4,
        adapter=WHEAT_ADAPTER,
        supported_actions=_ONE_TIME_ACTIONS,
        supported_stages=_COMMON_STAGES,
        limitations=(
            "one-tile crop-only graph",
            "animal-feed value is not modeled",
            "does not choose whether to buy wheat as a commodity",
        ),
    ),
    "melon_investment": DecisionGraphDescriptor(
        graph_id="melon_investment",
        display_name="Watermelon investment",
        crop="MELON",
        lifecycle="one-time-crop",
        parameter_namespace="PointPriceParameters",
        seed_cost=80,
        planning_horizon=10,
        adapter=MELON_ADAPTER,
        supported_actions=_ONE_TIME_ACTIONS,
        supported_stages=_COMMON_STAGES,
        limitations=(
            "one-tile crop-only graph",
            "does not model sell-versus-hold timing",
            "does not select among crops or shared capacity",
        ),
    ),
    "tomato_crop": DecisionGraphDescriptor(
        graph_id="tomato_crop",
        display_name="Tomato crop",
        crop="TOMATO",
        lifecycle="ongoing-crop",
        parameter_namespace="OngoingCropParameters",
        seed_cost=50,
        planning_horizon=11,
        adapter=TOMATO_ADAPTER,
        supported_actions=_ONE_TIME_ACTIONS,
        supported_stages=_COMMON_STAGES,
        limitations=(
            "ongoing-crop graph with repeated production",
            "does not select among crops or shared capacity",
            "does not model a general market-timing policy",
        ),
    ),
    "strawberry_crop": DecisionGraphDescriptor(
        graph_id="strawberry_crop",
        display_name="Strawberry crop",
        crop="STRAWBERRY",
        lifecycle="ongoing-crop",
        parameter_namespace="OngoingCropParameters",
        seed_cost=100,
        planning_horizon=16,
        adapter=STRAWBERRY_ADAPTER,
        supported_actions=_ONE_TIME_ACTIONS,
        supported_stages=_COMMON_STAGES,
        limitations=(
            "ongoing-crop graph with repeated production",
            "does not select among crops or shared capacity",
            "does not model a general market-timing policy",
        ),
    ),
}


def graph_descriptors() -> tuple[DecisionGraphDescriptor, ...]:
    """Return descriptors in a stable order for reports and UI consumers."""
    return tuple(GRAPH_REGISTRY.values())


def get_graph_descriptor(graph_id: str) -> DecisionGraphDescriptor:
    """Return one registered graph or fail closed for an unknown graph."""
    try:
        return GRAPH_REGISTRY[graph_id]
    except KeyError as error:
        raise ValueError(f"unknown decision graph: {graph_id}") from error


def bind_registered_graphs(
    target_root: str | PathLike[str] | None = None,
) -> dict[str, TargetBinding]:
    """Bind every registered graph to the same explicit target checkout.

    Binding is the only operation here.  It imports policies and records their
    provenance, but it does not run a simulator or apply any action.
    """
    return {
        descriptor.graph_id: bind_target(target_root, adapter=descriptor.adapter)
        for descriptor in graph_descriptors()
    }
