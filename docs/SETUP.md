# Release setup for Action-Semver-Control

This guide walks through adopting Action-Semver-Control in a repository you do not maintain personally. No tribal knowledge required.

## What you need

| Item | Purpose |
|------|---------|
| **GitHub App** (yours) | Verified commits and PRs that satisfy branch protection |
| **`GH_APP_ID`** secret | Numeric App ID from the app settings page |
| **`GH_APP_PRIVATE_KEY`** secret | PEM contents from **Generate a private key** |
| **`auto_semver_config.yml`** | Branch suffixes, version files, changelog groups |
| **Caller workflows** | Thin wrappers that invoke reusable workflows `@v1` |

Action-Semver-Control is listed on the [GitHub Marketplace](https://github.com/marketplace/actions/auto-semver-bumper) for discovery. Marketplace does not install secrets or workflows — follow this guide after adding the action.

## Quick setup (CLI)

From your consumer repository:

```bash
uvx --from git+https://github.com/GuyErreich/Action-Semver-Control auto-semver setup
```

The wizard will:

1. Print a **prefilled GitHub App registration URL**
2. Prompt for App ID and private key path
3. Write `GH_APP_ID` and `GH_APP_PRIVATE_KEY` via `gh secret set`
4. Scaffold `auto_semver_config.yml` and caller workflows (if missing)

Flags: `--dry-run`, `--skip-secrets`, `--skip-scaffold`, `--open-browser`.

## Manual setup

### 1. Register the GitHub App

Open the prefilled registration URL (permissions: **Contents** and **Pull requests** read/write, webhooks off):

```
https://github.com/settings/apps/new?name=Auto+Semver+Bot&description=Signed+commits+and+PRs+for+Action-Semver-Control&url=https%3A%2F%2Fgithub.com%2FGuyErreich%2FAction-Semver-Control&public=true&webhook_active=false&contents=write&pull_requests=write
```

Or regenerate links for your repo:

```bash
python scripts/generate_onboarding_links.py --owner YOUR_ORG --repo YOUR_REPO --branch master
```

Note the **App ID** (not the installation ID). Generate and download a **private key** (`.pem`).

### 2. Install the app on your repository

App settings → **Install App** → select your account/org → grant access to the target repository.

### 3. Set repository secrets

```bash
gh secret set GH_APP_ID --repo YOUR_ORG/YOUR_REPO
gh secret set GH_APP_PRIVATE_KEY --repo YOUR_ORG/YOUR_REPO
```

Paste the numeric App ID and the full PEM file contents (including `BEGIN` / `END` lines).

### 4. Add caller workflows

**Option A — GitHub UI (prefilled PR):**

Use the deep links from `scripts/generate_onboarding_links.py` or the CLI setup output. They open the web editor with workflow YAML already filled in.

**Option B — copy minimal callers:**

`.github/workflows/auto-semver.yml`:

```yaml
name: Auto Semver Bump
on:
  pull_request:
    types: [closed]
    branches: [dev, staging, master]
permissions:
  contents: write
  pull-requests: write
jobs:
  bump:
    if: github.event.pull_request.merged == true
    uses: GuyErreich/Action-Semver-Control/.github/workflows/semver-bump.reusable.yml@v1
    secrets:
      app-id: ${{ secrets.GH_APP_ID }}
      app-private-key: ${{ secrets.GH_APP_PRIVATE_KEY }}
```

`.github/workflows/promote.yml` (optional manual promotion):

```yaml
name: Manual Semver Promotion
on:
  workflow_dispatch:
    inputs:
      from_tag:
        required: true
        type: string
      to_branch:
        required: true
        default: staging
        type: choice
        options: [staging, master]
      dry_run:
        required: false
        default: false
        type: boolean
permissions:
  contents: write
jobs:
  promote:
    uses: GuyErreich/Action-Semver-Control/.github/workflows/semver-promote.reusable.yml@v1
    with:
      from_tag: ${{ inputs.from_tag }}
      to_branch: ${{ inputs.to_branch }}
      dry_run: ${{ inputs.dry_run }}
    secrets:
      app-id: ${{ secrets.GH_APP_ID }}
      app-private-key: ${{ secrets.GH_APP_PRIVATE_KEY }}
```

### 5. Configure `auto_semver_config.yml`

Start from [`src/auto_semver/setup/templates/auto_semver_config.yml`](../src/auto_semver/setup/templates/auto_semver_config.yml). Adjust:

- `suffixes` — map your branch names (`dev`, `staging`, `master`, etc.)
- `version_files` — files Action-Semver-Control may update directly
- `promotions` — which channels auto-promote
- `commit_groups` — changelog grouping (see README)

### 6. Create channel branches

```bash
git checkout -b dev && git push -u origin dev
git checkout -b staging && git push -u origin staging
```

Keep `master` (or `main`) as production. Merge feature work into `dev`.

## Pinning policy

| Pin | When to use |
|-----|-------------|
| `@v1` | **Recommended** — floating major tag, updated on each production release |
| `@1.3.14` | Exact semver for reproducibility |
| `@<sha>` | Maximum control; pin in reusable workflow `action-ref` input |

Production releases of Action-Semver-Control force-update the `v1` tag to the latest stable release.

## Troubleshooting

### Workflow fails immediately: "Missing GitHub App secrets"

Set `GH_APP_ID` and `GH_APP_PRIVATE_KEY` on the repository. Re-run setup:

```bash
uvx --from git+https://github.com/GuyErreich/Action-Semver-Control auto-semver setup
```

### `create-github-app-token` fails

- Confirm the app is **installed** on this repository (not just created).
- Confirm `GH_APP_ID` is the **App ID**, not the installation ID.
- Confirm the PEM secret includes header/footer lines.

### Reusable workflow not found `@v1`

The `v1` tag is created on the first **production** release of Action-Semver-Control. Until then, pin `action-ref` to a commit SHA or release tag in your caller workflow, or wait for `v1` to exist.

### Commits blocked by branch protection

Use a GitHub App (not `GITHUB_TOKEN` alone). App commits via the action satisfy typical **required signed commits** rules when branch protection is configured for verified commits.

## Architecture

```mermaid
flowchart LR
  merge[PR merged to dev] --> caller[auto-semver.yml caller]
  caller --> reusable[semver-bump.reusable.yml@v1]
  reusable --> preflight[Preflight secrets]
  preflight --> appAuth[app-authentication]
  appAuth --> action[Action-Semver-Control@v1]
  action --> releasePR[Release PR + tag]
```
