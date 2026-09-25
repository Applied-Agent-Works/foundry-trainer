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
