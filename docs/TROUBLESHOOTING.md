# Troubleshooting

Common auto-semver issues and how to fix them.

## Version didn't bump after I merged a feature PR

**Expected behavior (two-phase flow):**

1. Merging a feature/fix PR to `dev` opens or updates a **release PR** (e.g. `Release 1.4.0-dev`).
2. The version on `dev` updates only when you **merge that release PR** (finalize + tag).

Check open release PRs before assuming the bump failed.

## Version regressed (e.g. 1.4.0 → 1.3.15)

**Causes:**

- Missing workflow **concurrency** block — parallel bump runs race on the same baseline.
- A fix PR merged while a release PR was open, before single-mode baseline fix shipped.

**Fix:** Add to your caller workflow (see [SETUP.md — Concurrent merges](SETUP.md#concurrent-merges--bump-queue)):

```yaml
concurrency:
  group: auto-semver-bump-${{ github.repository }}-${{ github.event.pull_request.base.ref }}
  cancel-in-progress: false
```

Run `auto-semver setup --check` locally to validate.

## Batch merge / merge queue broke semver

Multiple PRs merged at once start multiple bump workflows unless they share a concurrency queue. With `cancel-in-progress: true`, in-flight bumps are cancelled and version updates are lost.

**Fix:** Use `cancel-in-progress: false` so runs queue per target branch.

## Release PR body is full of checkboxes / template noise

Squash-merge commit bodies can contain PR template checklists. Configure:

```yaml
commit_groups:
  summary_mode: header_only
  ignore_line_patterns:
    - '^\[[ xX]\]'
```

Only the commit/PR title line appears in release notes.

## Multiple release PRs / stale `release/*` branches

| Setting | Behavior |
|---------|----------|
| `release.strategy: single` (default) | One open release PR; older owned PRs closed and branches deleted when `cleanup_merged: true` |
| `release.strategy: multi` | Keeps sibling release PRs; you choose which to merge |

New branches use prefix `auto-semver/release/` (configurable). Legacy `release/*` branches are cleaned only when lock + PR marker prove auto-semver ownership.

**One-time cleanup:**

```bash
python scripts/cleanup_release_branches.py --dry-run   # review
python scripts/cleanup_release_branches.py --apply     # delete owned merged/closed branches
```

## Can I merge multiple release PRs?

- **`single`:** No — superseded open release PRs are closed when a new bump runs.
- **`multi`:** Yes — each merge creates another release PR; pick one to finalize.

## Cumulative vs classic bump mode

| Mode | Example (`1.3.14` + 2 fixes + 1 feature) |
|------|------------------------------------------|
| `classic` (default) | `1.4.0` (minor resets patch) |
| `cumulative` (opt-in) | `1.4.16` (patch accumulates) |

Enable for consumers only:

```yaml
bump:
  mode: cumulative
```

Major bumps always reset to `X.0.0`.

## Auto-promotion failed or staging did not deploy

**Expected behavior:**

1. Merging the **release PR** to `dev` tags `X.Y.Z-dev` and auto-promotes to `staging`.
2. Promotion merges the **dev tag** into `staging` (not `staging` into `dev`).
3. On metadata conflicts (`.semver.lock`, `CHANGELOG.md`, `version_files`), **dev/rc wins**.
4. A metadata commit rewrites headers and version files to `-rc`, then tags `X.Y.Z-rc`.
5. Pushing `*.*.*-rc` triggers **Publish Release - Staging**.

**If promotion failed with merge conflicts:** check whether the conflict is outside semver metadata (e.g. `README.md`). Those require a manual merge. Metadata conflicts should auto-resolve.

**If the workflow was green but staging did not update:** older versions swallowed promotion errors; ensure you are on a build that fails finalize when auto-promote fails.

**If staging rules block direct push:** promotion uses fast-forward when possible, otherwise a single squash-style commit (no merge commit). Tag creation may require the **Create Release Tag** workflow with the GitHub App token.

**Do not reset/rebase staging to dev** to promote — that rewrites history. Merge-based promotion preserves the git graph.
