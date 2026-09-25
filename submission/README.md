# Carrot submission package

This directory is the packaging boundary for the current Foundry submission.
The notebooks remain the teaching and evidence record; this package contains
the promoted implementation, redacted recorded receipts, and the human-facing
demonstration. The integrated roles are Evidence Analyst v2 and Evidence
Analyst Judge v1. The Proposal Drafter v3 remains a bounded review-only role.

## Agent inventory

| Foundry role | Version | Package status |
|:---|:---:|:---|
| `evidence-analyst` | 2 | complete integration |
| `evidence-analyst-judge` | 1 | complete integration; recorded score 1.0 |
| `experiment-proposal-drafter` | 3 | complete integration; review-only authority |

## Build the submission

From the repository root:

```bash
python3 scripts/build_submission.py
```

From inside this directory, the same build is available as
`./build.sh`. The demo can be launched with `./run-demo.sh`.

The backend can be started separately with `./run-backend.sh`; it listens on
port 5100. Its Carrot run endpoint invokes the approved local Python evaluator
against an isolated pinned Kaggriculture checkout and returns the actual
simulator, clean-audit, and immutable-packet receipt. Wheat, Watermelon, and
Foundry transport remain separate downstream adapters. The backend requires
the repository root, `.venv`, the approved contract, and the pinned checkout;
the standalone web publish does not copy those runtime dependencies.

The command performs four checks:

1. compiles the promoted `analyst/` and `evaluator/` Python sources;
2. imports both packages from the repository source tree;
3. validates the checked-in redacted analyst response against its fixture; and
4. publishes the standalone Blazor WebAssembly demo to `submission/dist/web/`.

The generated `submission/dist/` directory is disposable and ignored by Git.
The generated `manifest.json` records the source commit, promoted source files,
fixture checksums, and build commands. It intentionally does not copy notebooks,
credentials, connection strings, raw packets, or the Kaggriculture checkout.

## Demonstration

```bash
dotnet run --project submission/demo/demo.csproj
```

Open the printed local URL. The first screen is a deterministic, redacted
receipt-backed human-in-the-loop surface. Select **Evidence Analyst** to discuss
packet-backed facts, then **Evidence Analyst Judge** to inspect the independent
quality result, and finally **Proposal Drafter** to frame one bounded next test.
The acknowledgement checkbox is deliberate: neither role can approve a
candidate, change policy source, run the simulator, or silently expand the
experiment envelope.

The UI is a recorded-receipt review surface for the already-completed analyst
and judge integrations, plus a bounded live Carrot smoke-run control. It does
not expose credentials, mutate Foundry, or edit Kaggriculture policy source.
The Proposal Drafter is displayed as a completed review-only role: it can frame
one bounded next test, but it cannot approve or mutate anything. The UI and
review controls preserve that authority boundary.
