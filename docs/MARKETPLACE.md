# GitHub Marketplace

Action-Semver-Control is published as **Auto Semver Bumper** on the [GitHub Marketplace](https://github.com/marketplace/actions/auto-semver-bumper).

## Maintainer checklist (each production release)

1. Merge to `master` and tag `X.Y.Z` (no `-dev` / `-rc` suffix).
2. `publish-production.yml` creates the GitHub Release and force-updates the floating **`v1`** tag.
3. Open [Marketplace listing](https://github.com/marketplace/actions/new) (or edit existing) and publish from the new release tag.
4. Confirm `action.yml` includes `branding.icon` and `branding.color`.

Consumers should pin caller workflows at `@v1`. Exact semver pins (`@1.3.14`) and SHA pins remain supported via the reusable workflow `action-ref` input.
