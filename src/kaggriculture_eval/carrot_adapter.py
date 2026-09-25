"""Legacy explicit adapter for the existing Carrot Tuner."""

from .adapters import PolicyAdapter


CARROT_ADAPTER = PolicyAdapter(
    adapter_id="carrot-v1",
    shared_relative_path="agents/carrot/shared.py",
    policy_id="target.agents.carrot.shared.carrot_decision_agent",
    opponent_id="target.agents.carrot.shared.carrot_conveyor_agent",
    policy_attribute="carrot_decision_agent",
    opponent_attribute="carrot_conveyor_agent",
    parameter_relative_path=None,
    parameter_type_attribute="CarrotParameters",
    default_parameters_attribute="DEFAULT_PARAMETERS",
    decision_mode="wrapper",
    opponent_mode="wrapper",
)

