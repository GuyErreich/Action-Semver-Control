#!/usr/bin/env bash
# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Refresh pending lockfiles with the runner's uv or npm.
# When a CLI is not on PATH, ask the action image to patch only the project version.

set -euo pipefail

pending="${RUNNER_TEMP:?RUNNER_TEMP is required}/auto-semver-pending.json"
if [[ ! -f "${pending}" ]]; then
  echo "No pending release state; skipping host lock sync"
  exit 0
fi

cd "${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"

mapfile -t rows < <(python3 -c '
import json
import sys

pending = json.load(open(sys.argv[1], encoding="utf-8"))
print(pending.get("workflow", ""))
for lock in pending.get("locks", []):
    print(lock["ecosystem"])
' "${pending}")

workflow="${rows[0]:-}"
if [[ "${workflow}" == "finalize" || "${workflow}" == "dry-run" || "${workflow}" == "" ]]; then
  echo "Pending workflow ${workflow:-<empty>} has no host lock sync"
  exit 0
fi

missing=()
for ecosystem in "${rows[@]:1}"; do
  case "${ecosystem}" in
    uv)
      if command -v uv >/dev/null 2>&1; then
        echo "Running host uv lock"
        env -u UV_FROZEN uv lock
      else
        missing+=(uv)
      fi
      ;;
    npm)
      if command -v npm >/dev/null 2>&1; then
        echo "Running host npm install --package-lock-only"
        npm install --package-lock-only
      else
        missing+=(npm)
      fi
      ;;
    *)
      echo "No host command for ecosystem ${ecosystem}; leaving that lock unchanged" >&2
      ;;
  esac
done

if [[ "${#missing[@]}" -eq 0 ]]; then
  exit 0
fi

AUTO_SEMVER_PATCH_ECOSYSTEMS=$(IFS=,; echo "${missing[*]}")
export AUTO_SEMVER_PHASE=patch
export AUTO_SEMVER_PATCH_ECOSYSTEMS
echo "Patching project versions for: ${AUTO_SEMVER_PATCH_ECOSYSTEMS}"
bash "${GITHUB_ACTION_PATH:?GITHUB_ACTION_PATH is required}/scripts/action-engine.sh"
