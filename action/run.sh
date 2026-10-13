#!/usr/bin/env bash
# Copyright (c) 2025-2026 Guy Erreich
#
# SPDX-License-Identifier: GPL-3.0-or-later

# Install auto-semver-control for this action checkout and run it in the caller
# workspace. Invoked by the root action and by action/action.yml. Do not locate
# the package with a relative `uses:` path: GitHub resolves that in the caller
# repository, not in this action checkout.

set -euo pipefail

if [[ -z "${GITHUB_ACTION_PATH:-}" ]]; then
  echo "auto-semver: GITHUB_ACTION_PATH is not set" >&2
  exit 1
fi

if [[ -f "${GITHUB_ACTION_PATH}/pyproject.toml" ]]; then
  pkg="${GITHUB_ACTION_PATH}"
else
  pkg="$(cd "${GITHUB_ACTION_PATH}/.." && pwd)"
fi

if [[ ! -f "${pkg}/pyproject.toml" ]]; then
  echo "auto-semver: pyproject.toml not found from ${GITHUB_ACTION_PATH}" >&2
  exit 1
fi

if [[ -z "${PYTHON_BIN:-}" ]]; then
  echo "auto-semver: PYTHON_BIN is not set" >&2
  exit 1
fi

uv_version="$(tr -d '[:space:]' < "${pkg}/.uv-version")"
install_dir="${RUNNER_TEMP}/auto-semver-uv"
venv="${RUNNER_TEMP}/auto-semver-venv"
curl -LsSf "https://astral.sh/uv/${uv_version}/install.sh" \
  | env UV_INSTALL_DIR="${install_dir}" UV_NO_MODIFY_PATH=1 sh
pep="$(
  AUTO_SEMVER_PKG="${pkg}" PYTHONPATH="${pkg}/src" "${PYTHON_BIN}" -c \
    'import os, tomllib; from pathlib import Path; from auto_semver.lock_sync.pep440 import to_pep440; raw = tomllib.loads(Path(os.environ["AUTO_SEMVER_PKG"], "pyproject.toml").read_text())["project"]["version"]; print(to_pep440(raw))'
)"
uv="${install_dir}/uv"
# Pin the published release for this checkout. Never install the unrelated
# PyPI project named auto-semver. Fall back to this checkout until publish.
if ! "${uv}" venv --python "${PYTHON_BIN}" "${venv}" \
  || ! "${uv}" pip install --python "${venv}/bin/python" --prerelease explicit "auto-semver-control==${pep}"; then
  echo "auto-semver-control==${pep} is not on PyPI; installing this checkout"
  rm -rf "${venv}"
  UV_PROJECT_ENVIRONMENT="${venv}" \
    "${uv}" sync --frozen --no-dev --no-editable --directory "${pkg}" --python "${PYTHON_BIN}"
fi

bin="${RUNNER_TEMP}/auto-semver-venv/bin/auto-semver"
args=(--github-token "${AUTO_SEMVER_TOKEN}")
if [[ "${AUTO_SEMVER_DEBUG:-}" == "true" ]]; then
  args+=(--debug)
fi
if [[ "${AUTO_SEMVER_SIGNED:-}" == "true" ]]; then
  args+=(--signed-commits)
fi
if [[ "${AUTO_SEMVER_ACTION:-bump}" == "promote" ]]; then
  args+=(promote --to-branch "${AUTO_SEMVER_TO_BRANCH}" --from-tag "${AUTO_SEMVER_FROM_TAG}")
  if [[ "${AUTO_SEMVER_DRY_RUN:-}" == "true" ]]; then
    args+=(--dry-run)
  fi
fi

cd "${GITHUB_WORKSPACE}"
env -u UV_PROJECT_ENVIRONMENT -u UV_FROZEN "${bin}" "${args[@]}"
