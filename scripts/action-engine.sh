#!/usr/bin/env bash
# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: GPL-3.0-or-later
# Run one auto-semver phase inside the action image.
# The image uv is not used on consumer lockfiles; lock CLIs run on the runner.

set -euo pipefail

phase="${AUTO_SEMVER_PHASE:-all}"
action_path="${GITHUB_ACTION_PATH:?GITHUB_ACTION_PATH is required}"
workspace="${GITHUB_WORKSPACE:?GITHUB_WORKSPACE is required}"
runner_temp="${RUNNER_TEMP:?RUNNER_TEMP is required}"
image="auto-semver-action:local"

docker build -f "${action_path}/Dockerfile" -t "${image}" "${action_path}"

args=(--phase "${phase}")
if [[ "${INPUT_ACTION:-bump}" == "promote" ]]; then
  args+=(promote)
  if [[ -n "${INPUT_TO_BRANCH:-}" ]]; then
    args+=(--to-branch="${INPUT_TO_BRANCH}")
  fi
  if [[ -n "${INPUT_FROM_TAG:-}" ]]; then
    args+=(--from-tag="${INPUT_FROM_TAG}")
  fi
  if [[ "${INPUT_DRY_RUN:-false}" == "true" ]]; then
    args+=(--dry-run)
  fi
fi
if [[ -n "${INPUT_GITHUB_TOKEN:-}" ]]; then
  args+=(--github-token="${INPUT_GITHUB_TOKEN}")
fi
if [[ "${INPUT_SIGNED_COMMITS:-false}" == "true" ]]; then
  args+=(--signed-commits)
fi
if [[ "${INPUT_DEBUG:-false}" == "true" ]]; then
  args+=(--debug)
fi

docker_args=(
  --rm
  --user "$(id -u):$(id -g)"
  -e HOME=/tmp
  -e GITHUB_WORKSPACE=/github/workspace
  -e AUTO_SEMVER_PENDING=/github/runner_temp/auto-semver-pending.json
  -v "${workspace}:/github/workspace"
  -v "${runner_temp}:/github/runner_temp"
  -w /github/workspace
)

if [[ -n "${AUTO_SEMVER_PATCH_ECOSYSTEMS:-}" ]]; then
  docker_args+=(-e "AUTO_SEMVER_PATCH_ECOSYSTEMS=${AUTO_SEMVER_PATCH_ECOSYSTEMS}")
fi

while IFS='=' read -r name _; do
  case "${name}" in
    GITHUB_EVENT_PATH) ;;
    GITHUB_*) docker_args+=(-e "${name}") ;;
  esac
done < <(env)

event_path="${GITHUB_EVENT_PATH:-}"
if [[ -n "${event_path}" && -f "${event_path}" ]]; then
  docker_args+=(-e GITHUB_EVENT_PATH=/github/workflow/event.json)
  docker_args+=(-v "${event_path}:/github/workflow/event.json:ro")
fi

docker run "${docker_args[@]}" "${image}" "${args[@]}"
