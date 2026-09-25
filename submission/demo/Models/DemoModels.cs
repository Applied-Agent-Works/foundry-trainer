namespace demo.Models;

/// <summary>
/// A deliberately small receipt-backed transport seam. The real Foundry
/// transport can implement the same operations without changing the UI.
/// </summary>
public sealed record AgentProfile(
    string Id,
    string ShortName,
    string DisplayName,
    string Description,
    string Status);

public sealed record ChatMessage(string Role, string Text);

public sealed class RunPlan
{
    public string GraphId { get; set; } = "carrot_investment";
    public string Crop { get; set; } = "Carrot";
    public string ParameterName { get; set; } = "seed_opportunity_value";
    public double BaselineValue { get; set; } = 20;
    public double ProposedValue { get; set; } = 40;
    public string Seeds { get; set; } = "42";
    public bool SeatOneSelected { get; set; } = true;
    public bool SeatTwoSelected { get; set; } = true;
    public string SeatOneRole { get; set; } = "our_agent";
    public string SeatTwoRole { get; set; } = "opponent";
    public string Seats => string.Join(", ", new[] { SeatOneSelected ? "1" : null, SeatTwoSelected ? "2" : null }.Where(value => value is not null));
    public int Steps { get; set; } = 720;
    public string Opponent { get; set; } = "deterministic conveyor";
    public string OpponentMode { get; set; } = "deterministic_conveyor";
    public string ExecutionMode { get; set; } = "full_simulator";
    public string DivergenceStrategy { get; set; } = "first_action_then_suffix";
    public bool CleanAuditRequired { get; set; } = true;
    public string Status { get; set; } = "draft · pending human review";
    public string LastAction { get; set; } = "No execution requested";
}

public sealed class WorkbenchState
{
    public RunPlan Plan { get; } = new();
    public RunResultSummary? LastRunResult { get; private set; }
    public bool HasRunResult => LastRunResult is not null;
    public string SelectedAgentId { get; set; } = "evidence-analyst";
    public string Decision { get; set; } = "pending_human_review";
    public IReadOnlyList<RunStage> RunStages => runStages;
    public int CurrentStageIndex => runStages.FindIndex(stage => stage.Status == "current");
    private List<RunStage> runStages =
    [
        new("plan", "Plan validated", "complete", "The proposed envelope is structurally valid."),
        new("baseline", "Baseline prepared", "current", "Ready to submit the approved local run."),
        new("simulate", "Inner loop executed", "pending", "Simulator has not been started."),
        new("divergence", "Divergence analyzed", "pending", "No candidate result is available yet."),
        new("audit", "Clean audit completed", "pending", "A full independent rerun is required."),
        new("packet", "Evidence packet assembled", "pending", "Evidence is created only after audits pass."),
        new("foundry", "Foundry review completed", "pending", "The three Foundry roles remain downstream of the packet."),
    ];

    public void RequestRun()
    {
        runStages = runStages.Select((stage, index) => index == 0
            ? stage with { Status = "complete", Detail = "The proposed envelope was validated." }
            : index == 1
                ? stage with { Status = "current", Detail = "Backend execution requested; waiting for explicit simulator adapter." }
                : stage with { Status = "pending" }).ToList();
    }

    public string AdvanceStage()
    {
        var current = CurrentStageIndex;
        if (current < 0) return "All planned stages are complete.";
        runStages[current] = runStages[current] with { Status = "complete", Detail = "Completed through the guided execution control." };
        if (current + 1 < runStages.Count)
        {
            runStages[current + 1] = runStages[current + 1] with { Status = "current", Detail = "Current guided step." };
            return $"Completed {runStages[current].Title}; ready for {runStages[current + 1].Title}.";
        }
        return "Completed the final planned stage.";
    }

    public string RetreatStage()
    {
        var current = CurrentStageIndex;
        var completed = current < 0 ? runStages.Count - 1 : current - 1;
        if (completed <= 0) return "The plan-validation stage is the first recorded stage.";
        runStages[completed] = runStages[completed] with { Status = "current", Detail = "Returned here by the human reviewer." };
        for (var index = completed + 1; index < runStages.Count; index++)
            runStages[index] = runStages[index] with { Status = "pending", Detail = "Waiting for the preceding step." };
        return $"Returned to {runStages[completed].Title}.";
    }
    public IReadOnlyList<TestScenario> TestScenarios => scenarios;
    private List<TestScenario> scenarios =
    [
        new("baseline-reuse", "Baseline reuse", "Candidate follows the recorded action path", true),
        new("early-divergence", "Early divergence", "Candidate diverges at the first decision", true),
        new("late-divergence", "Late divergence", "Candidate diverges after a shared prefix", false),
        new("clean-audit", "Clean audit", "Fast result matches a fresh full run", true),
        new("provenance-guard", "Provenance guard", "Wrong source hash refuses cache reuse", true),
        new("agent-boundary", "Agent boundary", "Unsupported recommendation is refused", true),
    ];

    public int CoverageCount => TestScenarios.Count(item => item.Included);
    public int CoveragePercent => (int)Math.Round(CoverageCount * 100.0 / TestScenarios.Count);
    public IReadOnlyList<GraphOption> Graphs { get; } =
    [
        new("carrot_investment", "Carrot", "seed_opportunity_value", "carrot conveyor"),
        new("wheat_crop", "Wheat", "future_price_multiplier", "wheat conveyor"),
        new("melon_investment", "Watermelon / Melon", "future_price_multiplier", "melon conveyor"),
    ];

    public IReadOnlyList<ParameterEvidence> CarrotParameters { get; } =
    [
        new("supply_high_given_zero_ripe", "0.05", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("supply_high_given_one_to_three_ripe", "0.30", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("supply_high_given_four_plus_ripe", "0.70", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("low_price_multiplier", "0.60", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("high_price_multiplier", "1.20", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("low_price_base", "0.15", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("low_price_supply_weight", "0.65", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("high_price_base", "0.05", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("high_price_demand_weight", "0.02", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("high_price_supply_penalty", "0.30", "±10%", "inert in 60-game screen", "low", "No observed decision divergence in the fine screen."),
        new("seed_opportunity_value", "20.0", "10 / 40 / 60 / 80", "active above threshold; wider values harmful", "high", "Wider values changed rewards and produced audited divergences."),
        new("pass_utility", "0.0", "-25 / 25 / 50 / 100", "25+ changes decisions; clean audits passed", "high", "Positive values removed profitable planting in the recorded suite."),
    ];

    public IReadOnlyList<ParameterEvidence> ParametersForSelectedGraph
    {
        get
        {
            var source = Plan.GraphId switch
            {
                "wheat_crop" => new[] { new ParameterEvidence("future_price_multiplier", "1.0", "0.05 / 0.8 / 1.2", "0.05 diverged; 0.8 and 1.2 inert", "high", "A low value crossed the observed plant/pass threshold.") },
                "melon_investment" => new[] { new ParameterEvidence("future_price_multiplier", "1.0", "0.05 / 0.8 / 1.2", "0.05 diverged; 0.8 and 1.2 inert", "high", "A low value crossed the observed plant/pass threshold.") },
                _ => CarrotParameters.ToArray(),
            };
            return source.OrderByDescending(item => item.Priority == "high").ThenBy(item => item.Name).ToArray();
        }
    }

    public ParameterEvidence? SelectedParameterEvidence =>
        ParametersForSelectedGraph.FirstOrDefault(item => item.Name == Plan.ParameterName);

    public IReadOnlyList<double> ProposedValuesForSelectedParameter =>
        SelectedParameterEvidence is { } evidence ? ProposedValuesFor(evidence) : Array.Empty<double>();

    public bool LiveRunSupported =>
        Plan.GraphId == "carrot_investment"
        && Plan.ParameterName == "seed_opportunity_value"
        && new[] { 10d, 40d, 60d, 80d }.Contains(Plan.ProposedValue);

    public static IReadOnlyList<double> ProposedValuesFor(ParameterEvidence evidence) => evidence.Name switch
    {
        "pass_utility" => [-25, -12.5, 25, 50, 100],
        "seed_opportunity_value" => [10, 40, 60, 80, 100],
        "supply_high_given_zero_ripe" => [0, 0.025, 0.075, 0.1, 0.15],
        "supply_high_given_one_to_three_ripe" => [0.15, 0.225, 0.375, 0.45, 0.6],
        "supply_high_given_four_plus_ripe" => [0.35, 0.525, 0.775, 0.875, 1.0],
        "low_price_multiplier" => [0.3, 0.45, 0.75, 0.9, 1.2],
        "high_price_multiplier" => [0.6, 0.9, 1.5, 1.8, 2.4],
        "low_price_base" => [0, 0.075, 0.1875, 0.225, 0.3],
        "low_price_supply_weight" => [0.325, 0.4875, 0.8125, 0.975, 1.0],
        "high_price_base" => [0, 0.025, 0.0625, 0.075, 0.1],
        "high_price_demand_weight" => [0, 0.01, 0.025, 0.03, 0.04],
        "high_price_supply_penalty" => [0.15, 0.225, 0.375, 0.45, 0.6],
        _ => [evidence.BaselineValue(), evidence.BaselineValue()],
    };

    public static ParameterInfluence InfluenceFor(string parameterName) => parameterName switch
    {
        "supply_high_given_zero_ripe" or "supply_high_given_one_to_three_ripe" or "supply_high_given_four_plus_ripe" => new(
            [new("visible ripe-carrot count", "fixed")],
            [new("low/high price probabilities", "derived"), new("expected sale price", "derived")],
            "This is one branch of the supply belief. It changes how likely the agent thinks high supply is, which can make the expected price look better or worse.",
            [new("supply_high_given_zero_ripe", "parameter"), new("supply_high_given_one_to_three_ripe", "parameter"), new("supply_high_given_four_plus_ripe", "parameter")]),
        "low_price_multiplier" or "high_price_multiplier" => new(
            [new("low/high price probability", "derived")],
            [new("expected sale price", "derived")],
            "This changes the payout used for one price scenario. Its effect matters only when that price scenario has some probability.",
            [new("low_price_multiplier", "parameter"), new("high_price_multiplier", "parameter")]),
        "low_price_base" or "low_price_supply_weight" or "high_price_base" or "high_price_demand_weight" or "high_price_supply_penalty" => new(
            [new("supply probability", "derived"), new("known and future demand", "fixed")],
            [new("low/high price probabilities", "derived")],
            "This changes how the model turns supply and demand clues into price probabilities. Those probabilities then feed the expected sale price.",
            [new("low_price_base", "parameter"), new("low_price_supply_weight", "parameter"), new("high_price_base", "parameter"), new("high_price_demand_weight", "parameter"), new("high_price_supply_penalty", "parameter")]),
        "seed_opportunity_value" => new(
            [new("expected sale price", "derived"), new("baseline harvest yield", "fixed")],
            [new("plant utility", "derived"), new("plant/pass threshold", "derived")],
            "This is the value the agent assigns to keeping the seed for later. Increasing it makes planting harder to justify.",
            [new("pass_utility", "parameter")]),
        "pass_utility" => new(
            [new("plant utility", "derived")],
            [new("final plant/pass action", "derived")],
            "This is the score required before planting is preferred. Increasing it makes passing easier to choose.",
            [new("seed_opportunity_value", "parameter")]),
        _ => new(
            [new("observed game state", "fixed")],
            [new("next decision stage", "derived")],
            "This parameter changes a bounded part of the decision model. Its broader effect still needs direct evidence.",
            []),
    };

    public void ReplaceScenarios(IEnumerable<TestScenario> replacement) => scenarios = replacement.ToList();

    public void ApplyBackendReceipt(IReadOnlyList<RunStage> stages, RunResultSummary result, string action)
    {
        // The backend receipt is atomic, but the workbench presents its facts
        // as a guided review: baseline is complete and the selected candidate's
        // inner-loop result is the next section for the human to advance.
        runStages = runStages.Select(stage => stage.Id switch
        {
            "plan" => stage with { Status = "complete", Detail = "The approved plan passed validation." },
            "baseline" => stage with { Status = "complete", Detail = "The validated baseline is ready for comparison." },
            "simulate" => stage with { Status = "current", Detail = "The selected candidate result is ready to review." },
            _ => stage with { Status = "pending", Detail = "Waiting for the preceding review step." },
        }).ToList();
        LastRunResult = result;
        Plan.Status = "completed · real simulator receipt";
        Plan.LastAction = action;
    }

    public void ApplyStageReceipt(IReadOnlyList<RunStage> stages, string action)
    {
        runStages = stages.ToList();
        Plan.LastAction = action;
    }

    public void RecordRunResult(RunResultSummary result, string action)
    {
        LastRunResult = result;
        Plan.Status = "completed · real simulator receipt";
        Plan.LastAction = action;
    }
}

public sealed record TestScenario(string Id, string Title, string Description, bool Included);
public sealed record GraphOption(string Id, string DisplayName, string ParameterName, string Opponent);
public sealed record ParameterEvidence(string Name, string Baseline, string Tested, string Result, string Priority, string Why);
public sealed record InfluenceNode(string Label, string Kind);
public sealed record ParameterInfluence(IReadOnlyList<InfluenceNode> Upstream, IReadOnlyList<InfluenceNode> Downstream, string Explanation, IReadOnlyList<InfluenceNode> Related);
public static class ParameterEvidenceExtensions
{
    public static double BaselineValue(this ParameterEvidence evidence) =>
        double.TryParse(evidence.Baseline, out var value) ? value : 0;
}
public sealed record RunStage(string Id, string Title, string Status, string Detail);
public sealed record RunResultSummary(
    string ParameterName,
    double BaselineValue,
    int MatchCount,
    int CandidateCount,
    double BestCandidateValue,
    double BestMeanDecisionDelta,
    int BestDivergenceCount,
    bool AuditsPassed,
    string PacketPath)
{
    public string PlainEnglish =>
        $"We tested {CandidateCount} values against the baseline of {BaselineValue:0.##} across {MatchCount} matches. " +
        $"The strongest observed average change was at {BestCandidateValue:0.##}, with a reward difference of {BestMeanDecisionDelta:+0.##;-0.##;0}. " +
        $"That value diverged in {BestDivergenceCount} match{(BestDivergenceCount == 1 ? "" : "es")}. " +
        (AuditsPassed ? "Every result passed its clean audit." : "The clean-audit gate did not pass.");
}

public interface IAgentConversation
{
    IReadOnlyList<AgentProfile> Agents { get; }
    AgentProfile GetAgent(string id);
    IReadOnlyList<ChatMessage> StartConversation(string id);
    string Reply(AgentProfile agent, string question);
}

public sealed class DemoConversationService : IAgentConversation
{
    private static readonly AgentProfile[] Profiles =
    [
        new("evidence-analyst", "EA", "Evidence Analyst", "Explains packet-backed facts · v2", "COMPLETE · v2"),
        new("evidence-analyst-judge", "EJ", "Evidence Analyst Judge", "Scores grounding and limits · v1", "COMPLETE · v1"),
        new("experiment-proposal-drafter", "PD", "Proposal Drafter", "Frames one bounded next test · v3", "COMPLETE · v3"),
    ];

    public IReadOnlyList<AgentProfile> Agents => Profiles;

    public AgentProfile GetAgent(string id) =>
        Profiles.FirstOrDefault(agent => agent.Id == id) ?? Profiles[0];

    public IReadOnlyList<ChatMessage> StartConversation(string id)
    {
        var agent = GetAgent(id);
        return agent.Id switch
        {
            "evidence-analyst-judge" =>
            [
                new("agent", "I independently judged the recorded analyst response against the redacted brief."),
                new("agent", "Overall score: 1.0. Grounding, citations, limitations, boundedness, review boundary, and usefulness all passed."),
            ],
            "experiment-proposal-drafter" =>
            [
                new("agent", "I can frame one bounded follow-up question from the accepted analyst handoff. I cannot approve it or change policy source."),
                new("agent", "The recorded one-seed result suggests candidate 80 is worth testing again, but it is not a ranking."),
            ],
            _ =>
            [
                new("agent", "The packet passed the deterministic gate and remains descriptive-only."),
                new("agent", "Candidates 10, 40, and 60 show mean paired delta 0 across 2 matches; candidate 80 shows mean paired delta 937 across 2 matches."),
            ],
        };
    }

    public string Reply(AgentProfile agent, string question)
    {
        var prompt = question.Length > 160 ? question[..160] + "…" : question;
        return agent.Id == "experiment-proposal-drafter"
            ? $"For “{prompt}”, I would preserve the current contract and propose one held-out seed/seat measurement. This remains pending human review; no experiment is approved."
            : agent.Id == "evidence-analyst-judge"
                ? $"For “{prompt}”, the recorded judge result is fully aligned with the redacted evidence and preserves the human-review boundary."
            : $"For “{prompt}”, the packet supports only a descriptive answer. I can cite the supplied aggregates and limitations, but I cannot rank candidates or recommend a policy value.";
    }
}
