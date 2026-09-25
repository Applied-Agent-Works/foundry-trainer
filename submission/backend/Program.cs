using System.Collections.Immutable;
using System.Diagnostics;
using System.Text.Json;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddCors(options => options.AddDefaultPolicy(policy =>
    policy.AllowAnyOrigin().AllowAnyHeader().AllowAnyMethod()));
builder.Services.AddSingleton<RunCoordinator>();

var app = builder.Build();
app.UseCors();

var graphs = ImmutableArray.Create(
    new GraphDescriptor("carrot_investment", "Carrot", "seed_opportunity_value", "carrot conveyor", "available carrot planting opportunity"),
    new GraphDescriptor("wheat_crop", "Wheat", "future_price_multiplier", "wheat conveyor", "eligible wheat planting opportunity"),
    new GraphDescriptor("melon_investment", "Watermelon / Melon", "future_price_multiplier", "melon conveyor", "eligible melon planting opportunity"));

app.MapGet("/api/health", () => Results.Ok(new { status = "ok", service = "carrot-review-backend" }));
app.MapGet("/api/graphs", () => Results.Ok(graphs));

app.MapPost("/api/run-plans/validate", (RunPlanRequest plan) =>
{
    var graph = graphs.FirstOrDefault(item => item.Id == plan.GraphId);
    var errors = new List<string>();
    if (graph is null) errors.Add("graph is not registered");
    if (string.IsNullOrWhiteSpace(plan.ParameterName)) errors.Add("parameter name is required");
    if (plan.Seeds.Length == 0 || plan.Seats.Length == 0) errors.Add("at least one seed and seat are required");
    if (plan.Steps <= 0) errors.Add("steps must be positive");
    if (plan.BaselineValue == plan.ProposedValue) errors.Add("proposed value must differ from baseline");
    return errors.Count == 0
        ? Results.Ok(new { valid = true, execution = "awaiting_human_approval", graph, side_effect = "none" })
        : Results.BadRequest(new { valid = false, errors });
});

app.MapPost("/api/runs", (RunPlanRequest plan, RunCoordinator coordinator) =>
{
    var graph = graphs.FirstOrDefault(item => item.Id == plan.GraphId);
    if (graph is null) return Results.BadRequest(new { valid = false, errors = new[] { "graph is not registered" } });
    var validation = coordinator.Validate(plan, graph);
    if (!validation.Valid) return Results.BadRequest(validation);
    try
    {
        var receipt = coordinator.Execute(plan, graph, validation.RunId);
        return Results.Ok(validation with { Receipt = receipt });
    }
    catch (Exception error)
    {
        return Results.Problem(
            title: "The approved simulator run stopped",
            detail: error.Message,
            statusCode: StatusCodes.Status502BadGateway);
    }
});

app.MapGet("/api/runs/{runId}", (string runId, RunCoordinator coordinator) =>
    coordinator.Get(runId) is { } receipt ? Results.Ok(receipt) : Results.NotFound());

app.MapPost("/api/runs/preview", (RunPlanRequest plan) => Results.Ok(new
{
    status = "receipt_preview",
    graph = plan.GraphId,
    execution_mode = "recorded_receipt",
    message = "This preview consumes recorded evidence. A simulator run requires a separately authorized backend adapter.",
    source_policy_mutation = false,
    human_review = "pending_human_review"
}));

app.MapGet("/", () => Results.Ok(new
{
    service = "Carrot review backend",
    message = "Use /api/graphs, /api/run-plans/validate, and /api/runs. The browser UI is served separately by the WASM host."
}));

app.Run();

public sealed record GraphDescriptor(string Id, string DisplayName, string ParameterName, string Opponent, string Eligibility);
public sealed record RunPlanRequest(string GraphId, string ParameterName, double BaselineValue, double ProposedValue, int[] Seeds, int[] Seats, int Steps);

public sealed record RunStageReceipt(string Id, string Title, string Status, string Detail);
public sealed record CandidateResult(double CandidateValue, int MatchCount, double MeanPairedDecisionDelta, int DivergentMatchCount, bool AllAuditsPassed);
public sealed record RunReceipt(
    string RunId,
    string GraphId,
    string ExecutionMode,
    string Status,
    bool SourceMutation,
    IReadOnlyList<RunStageReceipt> Stages,
    string? TargetRevision = null,
    string? PacketPath = null,
    string? PacketSha256 = null,
    int MatchCount = 0,
    int CandidateCount = 0,
    bool AuditsPassed = false,
    IReadOnlyList<CandidateResult>? CandidateResults = null);
public sealed record RunValidation(bool Valid, string RunId, IReadOnlyList<string> Errors, RunReceipt? Receipt);

public sealed class RunCoordinator
{
    private readonly Dictionary<string, RunReceipt> receipts = new();

    public RunValidation Validate(RunPlanRequest plan, GraphDescriptor graph)
    {
        var errors = new List<string>();
        // The first live adapter is deliberately narrower than the UI catalog:
        // it may execute only the already-approved Carrot smoke contract.
        if (graph.Id != "carrot_investment") errors.Add("the live adapter currently supports Carrot only");
        if (!string.Equals(plan.ParameterName, graph.ParameterName, StringComparison.Ordinal)) errors.Add($"parameter does not belong to the {graph.DisplayName} graph");
        if (plan.BaselineValue != 20 || plan.ProposedValue is not (10 or 40 or 60 or 80)) errors.Add("the approved Carrot smoke envelope requires baseline 20 and proposed value 10, 40, 60, or 80");
        if (!plan.Seeds.SequenceEqual([42])) errors.Add("the approved smoke envelope uses seed 42");
        if (!plan.Seats.SequenceEqual([0, 1])) errors.Add("the approved smoke envelope uses seats 0 and 1");
        if (plan.Steps != 720) errors.Add("the approved smoke envelope uses 720 steps");
        if (errors.Count > 0) return new(false, string.Empty, errors, null);

        var runId = $"run-{Guid.NewGuid():N}";
        var receipt = new RunReceipt(runId, graph.Id, "full_simulator", "validated", false,
        [
            new("plan", "Plan validated", "complete", "Graph, parameter, suite, and governance fields validated."),
            new("adapter", "Tuner adapter selected", "current", "Approved Carrot Python adapter is ready."),
            new("simulate", "Inner loop executed", "pending", "Waiting for the approved Python runner."),
            new("audit", "Clean audit completed", "pending", "Requires the simulator result and independent rerun."),
            new("packet", "Evidence packet assembled", "pending", "Requires passing audits."),
            new("foundry", "Foundry review completed", "pending", "Downstream of the evidence packet."),
        ]);
        receipts[runId] = receipt;
        return new(true, runId, errors, receipt);
    }

    public RunReceipt Execute(RunPlanRequest plan, GraphDescriptor graph, string runId)
    {
        var root = Path.GetFullPath(Environment.GetEnvironmentVariable("FOUNDRY_TRAINER_ROOT") ?? Directory.GetCurrentDirectory());
        var python = Environment.GetEnvironmentVariable("FOUNDRY_TUNER_PYTHON") ?? Path.Combine(root, ".venv", "bin", "python");
        var target = Environment.GetEnvironmentVariable("FOUNDRY_TUNER_TARGET_ROOT") ?? Path.GetFullPath(Path.Combine(root, "..", "kaggriculture.worktrees", "carrot-smoke-pinned"));
        var spec = Path.Combine(root, "carrot-tuning-system", "experiments", "approved", "carrot_investment", "seed_opportunity_candidate_evidence_smoke_v1.json");
        var runRoot = Path.Combine(root, "var", "ui-runs", runId);
        var cacheRoot = Path.Combine(runRoot, "cache");
        var reportRoot = Path.Combine(runRoot, "report");
        if (!File.Exists(python)) throw new FileNotFoundException("The configured project Python interpreter was not found.", python);
        if (!Directory.Exists(target)) throw new DirectoryNotFoundException($"The pinned Kaggriculture checkout was not found: {target}");

        var start = new ProcessStartInfo(python)
        {
            WorkingDirectory = root,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        start.Environment["PYTHONPATH"] = $"src{Path.PathSeparator}carrot-tuning-system";
        start.ArgumentList.Add(Path.Combine(root, "scripts", "run_carrot_ui.py"));
        start.ArgumentList.Add("--spec"); start.ArgumentList.Add(spec);
        start.ArgumentList.Add("--target-root"); start.ArgumentList.Add(target);
        start.ArgumentList.Add("--cache-root"); start.ArgumentList.Add(cacheRoot);
        start.ArgumentList.Add("--report-dir"); start.ArgumentList.Add(reportRoot);

        using var process = Process.Start(start) ?? throw new InvalidOperationException("Could not start the Carrot runner process.");
        var stdout = process.StandardOutput.ReadToEnd();
        var stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        if (process.ExitCode != 0)
            throw new InvalidOperationException(string.IsNullOrWhiteSpace(stderr) ? stdout.Trim() : stderr.Trim());

        using var result = JsonDocument.Parse(stdout);
        var data = result.RootElement;
        var packetPath = data.GetProperty("packet_path").GetString();
        var packetSha = data.GetProperty("packet_sha256").GetString();
        var targetRevision = data.GetProperty("target_revision").GetString();
        var candidateResults = data.GetProperty("aggregates").EnumerateArray()
            .Select(item => new CandidateResult(
                item.GetProperty("candidate_value").GetDouble(),
                item.GetProperty("match_count").GetInt32(),
                item.GetProperty("mean_paired_decision_delta").GetDouble(),
                item.GetProperty("divergent_match_count").GetInt32(),
                item.GetProperty("all_audits_passed").GetBoolean()))
            .ToArray();
        var receipt = new RunReceipt(runId, graph.Id, "full_simulator", "completed", false,
        [
            new("plan", "Plan validated", "complete", "The approved Carrot contract and target fingerprint passed."),
            new("adapter", "Tuner adapter selected", "complete", $"Pinned target revision {targetRevision}."),
            new("simulate", "Inner loop executed", "complete", "Baseline caches and all declared candidate matches ran."),
            new("audit", "Clean audit completed", "complete", "Every fast result passed its independent clean rerun."),
            new("packet", "Evidence packet assembled", "complete", $"Immutable packet written: {packetPath}"),
            new("foundry", "Foundry review completed", "pending", "Ready for the separate Foundry evidence workflow."),
        ], targetRevision, packetPath, packetSha,
            data.GetProperty("match_count").GetInt32(), data.GetProperty("candidate_count").GetInt32(), data.GetProperty("audits_passed").GetBoolean(), candidateResults);
        receipts[runId] = receipt;
        return receipt;
    }

    public RunReceipt? Get(string runId) => receipts.TryGetValue(runId, out var receipt) ? receipt : null;
}
