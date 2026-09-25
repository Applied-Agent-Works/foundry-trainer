#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export FOUNDRY_TRAINER_ROOT="$ROOT"
exec dotnet run --project "$ROOT/submission/backend/backend.csproj" --no-launch-profile --urls "http://0.0.0.0:5100" "$@"
