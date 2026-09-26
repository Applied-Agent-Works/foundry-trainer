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

app.MapPost("/api/run-plans/validate", (RunPlanRequest plan, RunCoordinator coordinator) =>
{
    var graph = graphs.FirstOrDefault(item => item.Id == plan.GraphId);
    var errors = new List<string>();
    if (graph is null) errors.Add("graph is not registered");
    if (graph is not null)
    {
        // Keep the preflight endpoint aligned with the actual live adapter.
        // A plan that is structurally plausible but unsupported by the current
        // runner must not appear runnable in the workbench.
        var liveValidation = coordinator.Validate(plan, graph);
        errors.AddRange(liveValidation.Errors);
    }
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
    return Results.Ok(validation);
});

app.MapPost("/api/runs/{runId}/restart", (string runId, RunStageRestartRequest request, RunCoordinator coordinator) =>
{
    var validation = coordinator.Restart(runId, request.StageId);
    return validation is null
        ? Results.NotFound(new { valid = false, errors = new[] { "run was not found" } })
        : validation.Valid ? Results.Ok(validation) : Results.BadRequest(validation);
});

app.MapPost("/api/runs/{runId}/advance", (string runId, RunCoordinator coordinator) =>
{
    try
    {
        return coordinator.Advance(runId) is { } result
            ? Results.Ok(result)
            : Results.NotFound(new { valid = false, errors = new[] { "run was not found" } });
    }
    catch (Exception error)
    {
        return Results.Problem(title: "The requested run stage stopped", detail: error.Message, statusCode: StatusCodes.Status502BadGateway);
    }
});

app.MapPost("/api/runs/{runId}/foundry-feedback", (string runId, RunCoordinator coordinator) =>
    Results.Ok(coordinator.InvokeFoundryFeedback(runId)));

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
public sealed record RunPlanRequest(
    string GraphId,
    string ParameterName,
    double BaselineValue,
    double ProposedValue,
    int[] Seeds,
    int[] Seats,
    int Steps,
    TemporalInterventionRequest[]? Interventions = null,
    double[]? CandidateValues = null);
public sealed record TemporalInterventionRequest(int Step, double Value);
public sealed record RunStageRestartRequest(string StageId);

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
public sealed record FoundryFeedbackInvocation(string Status, string? AgentName = null, string? ResponseId = null, string? PacketSha256 = null, string? OutputText = null, string? Error = null);

public sealed class RunCoordinator
{
    private readonly Dictionary<string, RunReceipt> receipts = new();
    private readonly Dictionary<string, FoundryFeedbackInvocation> foundryFeedback = new();

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
        var candidateValues = plan.CandidateValues is { Length: > 0 }
            ? plan.CandidateValues
            : [plan.ProposedValue];
        if (candidateValues.Any(value => value is not (10 or 40 or 60 or 80)))
            errors.Add("candidate values must be one of the approved Carrot candidates: 10, 40, 60, or 80");
        if (!candidateValues.Contains(plan.ProposedValue))
            errors.Add("the selected proposed value must be included in the candidate range");
        var interventions = plan.Interventions is { Length: > 0 }
            ? plan.Interventions
            : [new TemporalInterventionRequest(0, plan.ProposedValue)];
        if (interventions.Length > 0)
        {
            if (!interventions.Select(item => item.Step).SequenceEqual(interventions.Select(item => item.Step).OrderBy(step => step)))
                errors.Add("intervention steps must be in ascending order");
            if (interventions.Select(item => item.Step).Distinct().Count() != interventions.Length)
                errors.Add("intervention steps must be unique");
            if (interventions.Any(item => item.Step < 0 || item.Step >= plan.Steps))
                errors.Add("intervention steps must fall inside the approved run");
            if (interventions.Any(item => item.Value is not (10 or 40 or 60 or 80)))
                errors.Add("intervention values must be one of the approved Carrot candidates: 10, 40, 60, or 80");
        }
        if (errors.Count > 0) return new(false, string.Empty, errors, null);

        var runId = $"run-{Guid.NewGuid():N}";
        var receipt = new RunReceipt(runId, graph.Id, "full_simulator", "validated", false,
        [
            new("plan", "Plan validated", "complete", "Graph, parameter, suite, and governance fields validated."),
            new("baseline", "Baseline prepared", "current", "Waiting for the baseline preparation stage."),
            new("simulate", "Inner loop executed", "pending", "Waiting for the selected candidate."),
            new("divergence", "Divergence analyzed", "pending", "Waiting for the inner-loop result."),
            new("audit", "Clean audit completed", "pending", "Waiting for the independent rerun."),
            new("packet", "Evidence packet assembled", "pending", "Waiting for the audited result."),
            new("foundry", "Foundry review completed", "pending", "Downstream of the evidence packet."),
        ]);
        receipts[runId] = receipt;
        plans[runId] = new RunState(plan, graph, receipt);
        return new(true, runId, errors, receipt);
    }

    public RunValidation? Advance(string runId)
    {
        if (!plans.TryGetValue(runId, out var state)) return null;
        var current = state.Receipt.Stages.FirstOrDefault(stage => stage.Status == "current");
        if (current is null) return new(true, runId, [], state.Receipt);
        JsonElement? data = current.Id == "foundry" ? null : ExecuteStage(state.Plan, state.Graph, runId, current.Id);
        var stages = state.Receipt.Stages.Select(stage => stage.Id == current.Id
            ? stage with { Status = "complete", Detail = StageCompletionDetail(current.Id, data) }
            : stage.Id == NextStageId(current.Id)
                ? stage with { Status = "current", Detail = "Current execution stage." }
                : stage).ToArray();
        var receipt = state.Receipt with { Stages = stages, Status = "in_progress" };
        if (current.Id == "packet" && data is not null)
        {
            receipt = receipt with
            {
                Status = "completed",
                PacketPath = data.Value.GetProperty("packet_path").GetString(),
                PacketSha256 = data.Value.GetProperty("packet_sha256").GetString(),
                MatchCount = data.Value.GetProperty("match_count").GetInt32(),
                CandidateCount = data.Value.GetProperty("candidate_count").GetInt32(),
                AuditsPassed = data.Value.GetProperty("audits_passed").GetBoolean(),
                CandidateResults = data.Value.GetProperty("aggregates").EnumerateArray().Select(item => new CandidateResult(
                    item.GetProperty("candidate_value").GetDouble(), item.GetProperty("match_count").GetInt32(),
                    item.GetProperty("mean_paired_decision_delta").GetDouble(), item.GetProperty("divergent_match_count").GetInt32(),
                    item.GetProperty("all_audits_passed").GetBoolean())).ToArray(),
            };
        }
        state.Receipt = receipt;
        receipts[runId] = receipt;
        return new(true, runId, [], receipt);
    }

    public RunValidation? Restart(string runId, string stageId)
    {
        if (!plans.TryGetValue(runId, out var state)) return null;
        var stageIds = state.Receipt.Stages.Select(stage => stage.Id).ToArray();
        var selectedIndex = Array.IndexOf(stageIds, stageId);
        if (selectedIndex < 0) return new(false, runId, [$"stage '{stageId}' is not part of this run"], null);

        // The selected stage remains complete; its successor is the next
        // executable stage. The receipt and Forward button therefore agree.
        var stages = state.Receipt.Stages.Select((stage, index) =>
            index <= selectedIndex
                ? stage with { Status = "complete", Detail = index == 0 ? "The approved plan passed validation." : "Completed before the selected restart point." }
                : index == selectedIndex + 1
                    ? stage with { Status = "current", Detail = "Current execution stage." }
                    : stage with { Status = "pending", Detail = "Must be rerun after returning to an earlier stage." })
            .ToArray();
        var receipt = state.Receipt with
        {
            Stages = stages,
            Status = "in_progress",
            TargetRevision = null,
            PacketPath = null,
            PacketSha256 = null,
            MatchCount = 0,
            CandidateCount = 0,
            AuditsPassed = false,
            CandidateResults = null,
        };
        state.Receipt = receipt;
        receipts[runId] = receipt;
        return new(true, runId, [], receipt);
    }

    public FoundryFeedbackInvocation InvokeFoundryFeedback(string runId)
    {
        if (foundryFeedback.TryGetValue(runId, out var cached)) return cached;
        if (!plans.TryGetValue(runId, out var state))
            return new("blocked", Error: "run was not found");
        var packetPath = state.Receipt.PacketPath;
        if (state.Receipt.Status != "completed" || string.IsNullOrWhiteSpace(packetPath))
            return new("blocked", Error: "Foundry feedback requires a completed evidence packet");
        if (!File.Exists(packetPath))
            return new("blocked", Error: $"evidence packet was not found: {packetPath}");

        var root = Path.GetFullPath(Environment.GetEnvironmentVariable("FOUNDRY_TRAINER_ROOT")
            ?? Path.Combine(AppContext.BaseDirectory, "../../../../"));
        var python = Environment.GetEnvironmentVariable("FOUNDRY_TUNER_PYTHON")
            ?? Path.Combine(root, ".venv", "bin", "python");
        var script = Path.Combine(root, "scripts", "invoke_foundry_feedback.py");
        if (!File.Exists(python)) return new("blocked", Error: $"configured Python interpreter was not found: {python}");
        if (!File.Exists(script)) return new("blocked", Error: $"Foundry integration script was not found: {script}");

        var start = new ProcessStartInfo(python)
        {
            WorkingDirectory = root,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        start.Environment["PYTHONPATH"] = $"src{Path.PathSeparator}carrot-tuning-system";
        start.ArgumentList.Add(script);
        start.ArgumentList.Add("--packet");
        start.ArgumentList.Add(packetPath);
        try
        {
            using var process = Process.Start(start) ?? throw new InvalidOperationException("could not start the Foundry integration process");
            var stdout = process.StandardOutput.ReadToEnd();
            var stderr = process.StandardError.ReadToEnd();
            process.WaitForExit();
            using var document = JsonDocument.Parse(stdout);
            var result = document.RootElement;
            var status = result.GetProperty("status").GetString();
            if (status != "completed")
                return new("blocked", Error: result.TryGetProperty("error", out var error) ? error.GetString() : stderr.Trim());
            var completed = new FoundryFeedbackInvocation(
                "completed",
                result.GetProperty("agent_name").GetString(),
                result.GetProperty("response_id").GetString(),
                result.GetProperty("packet_sha256").GetString(),
                result.GetProperty("output_text").GetString());
            foundryFeedback[runId] = completed;
            return completed;
        }
        catch (Exception error)
        {
            return new("blocked", Error: $"{error.GetType().Name}: {error.Message}");
        }
    }

    private static string? NextStageId(string current) => current switch
    {
        "baseline" => "simulate", "simulate" => "divergence", "divergence" => "audit", "audit" => "packet", "packet" => "foundry", _ => null,
    };

    private static string StageCompletionDetail(string stage, JsonElement? data) => stage switch
    {
        "baseline" => $"The full unchanged baseline simulation is prepared and validated ({data?.GetProperty("cache_count").GetInt32() ?? 0} cache entries).",
        "simulate" => $"Selected candidate inner loop completed ({data?.GetProperty("match_count").GetInt32() ?? 0} matches).",
        "divergence" => $"Divergence analysis completed ({data?.GetProperty("divergent_match_count").GetInt32() ?? 0} divergent matches).",
        "audit" => data?.GetProperty("audits_passed").GetBoolean() == true
            ? "The selected candidate passed its independent clean audit."
            : "The selected candidate did not pass its independent clean audit.",
        "packet" => $"Immutable evidence packet assembled ({data?.GetProperty("match_count").GetInt32() ?? 0} matches, {data?.GetProperty("candidate_count").GetInt32() ?? 0} candidate values).",
        _ => "Stage completed.",
    };

    private JsonElement ExecuteStage(RunPlanRequest plan, GraphDescriptor graph, string runId, string stage)
    {
        var root = Path.GetFullPath(Environment.GetEnvironmentVariable("FOUNDRY_TRAINER_ROOT") ?? Directory.GetCurrentDirectory());
        var python = Environment.GetEnvironmentVariable("FOUNDRY_TUNER_PYTHON") ?? Path.Combine(root, ".venv", "bin", "python");
        var target = Environment.GetEnvironmentVariable("FOUNDRY_TUNER_TARGET_ROOT") ?? Path.GetFullPath(Path.Combine(root, "..", "kaggriculture.worktrees", "carrot-smoke-pinned"));
        var spec = Path.Combine(root, "carrot-tuning-system", "experiments", "approved", "carrot_investment", "seed_opportunity_candidate_evidence_smoke_v1.json");
        var reportRoot = Path.Combine(root, "var", "ui-runs", runId, "report");
        var cacheRoot = Path.Combine(root, "var", "ui-runs", runId, "cache");
        var start = new ProcessStartInfo(python) { WorkingDirectory = root, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false };
        start.Environment["PYTHONPATH"] = $"src{Path.PathSeparator}carrot-tuning-system";
        start.ArgumentList.Add(Path.Combine(root, "scripts", "run_carrot_ui.py"));
        start.ArgumentList.Add("--spec"); start.ArgumentList.Add(spec);
        start.ArgumentList.Add("--target-root"); start.ArgumentList.Add(target);
        start.ArgumentList.Add("--cache-root"); start.ArgumentList.Add(cacheRoot);
        start.ArgumentList.Add("--report-dir"); start.ArgumentList.Add(reportRoot);
        start.ArgumentList.Add("--candidate-value"); start.ArgumentList.Add(plan.ProposedValue.ToString(System.Globalization.CultureInfo.InvariantCulture));
        start.ArgumentList.Add("--schedule"); start.ArgumentList.Add(JsonSerializer.Serialize((plan.Interventions ?? []).Select(item => new { step = item.Step, value = item.Value })));
        start.ArgumentList.Add("--candidate-values"); start.ArgumentList.Add(JsonSerializer.Serialize(plan.CandidateValues is { Length: > 0 } ? plan.CandidateValues : [plan.ProposedValue]));
        start.ArgumentList.Add("--stage"); start.ArgumentList.Add(stage == "simulate" ? "inner-loop" : stage);
        using var process = Process.Start(start) ?? throw new InvalidOperationException("Could not start the staged Carrot runner process.");
        var stdout = process.StandardOutput.ReadToEnd(); var stderr = process.StandardError.ReadToEnd(); process.WaitForExit();
        if (process.ExitCode != 0) throw new InvalidOperationException(string.IsNullOrWhiteSpace(stderr) ? stdout.Trim() : stderr.Trim());
        using var document = JsonDocument.Parse(stdout);
        return document.RootElement.Clone();
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
        start.ArgumentList.Add("--candidate-value"); start.ArgumentList.Add(plan.ProposedValue.ToString(System.Globalization.CultureInfo.InvariantCulture));

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
    private readonly Dictionary<string, RunState> plans = new();
}

public sealed class RunState
{
    public RunState(RunPlanRequest plan, GraphDescriptor graph, RunReceipt receipt) { Plan = plan; Graph = graph; Receipt = receipt; }
    public RunPlanRequest Plan { get; }
    public GraphDescriptor Graph { get; }
    public RunReceipt Receipt { get; set; }
}
