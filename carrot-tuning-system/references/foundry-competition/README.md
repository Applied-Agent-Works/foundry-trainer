# Microsoft Virtual Agent-a-thon reference

This folder contains the official rules PDF supplied for the 2026 Microsoft
Virtual Agent-a-thon:

- [Official rules PDF](./EN-WBNR-SlideDeck-SREVM92894.pdf)
- Original source: <https://info.microsoft.com/rs/157-GQE-382/images/EN-WBNR-SlideDeck-SREVM92894-pdf.pdf?version=0>

## Requirements relevant to our Foundry plan

The rules say an eligible entry must include:

- an AI agent with a clear purpose and audience;
- a brief written description of the issue addressed, the agent's impact, and
  how it was built using Copilot Studio Lite, Copilot Studio, or Microsoft
  Foundry;
- screenshots, example interactions, and key lessons learned;
- a video no longer than three minutes and no larger than 150 MB that
  demonstrates innovation, impact, and usability; and
- an upload to the Founderz platform by the stated deadline.

Supporting documentation may be included in formats including PDF, PPTX,
DOCX, DOC, PPT, or TXT.

The judging criteria are innovation, usability, and impact. The rules do not
require Python, the Azure Python SDK, `azure-identity`,
`DefaultAzureCredential`, a custom deployment script, a hosted agent, or a
particular authentication implementation.

## Azure Identity decision

`azure-identity` is an implementation detail, not a competition requirement.
It is useful only if we choose to have Python code authenticate directly to
Foundry—for example, to run a read-only SDK inspection or create resources
programmatically. It is not needed merely to submit or demonstrate a Foundry
agent through the portal or Founderz materials.

Therefore:

- do not repair the shared Python environment solely to satisfy the contest;
- do not add Azure Identity to the submitted architecture unless the chosen
  implementation genuinely needs direct SDK authentication; and
- keep the current no-tools prompt-agent boundary independent of this optional
  local inspection path.

## Timing and interpretation notes

The PDF is dated for the 2026 contest and states an entry deadline of September
24, 2026. The extracted rules contain both Pacific Daylight Time and GMT
wording in different sections; use the Founderz submission platform's displayed
deadline or an official contest update for the authoritative operational time.

This summary is a project planning aid, not legal advice. The PDF and any
updated official rules remain authoritative.
