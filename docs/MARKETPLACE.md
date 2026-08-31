# GitHub Marketplace

Action-Semver-Control is published as **Auto Semver Bumper** on the [GitHub Marketplace](https://github.com/marketplace/actions/auto-semver-bumper).

## Maintainer checklist (each production release)

1. Merge to `master` and tag `X.Y.Z` (no `-dev` / `-rc` suffix).
2. `publish-production.yml` creates the GitHub Release and force-updates the floating **`v1`** tag.
3. Update the Marketplace listing from that production tag (UI only — there is no API for the Marketplace checkbox):
   - Edit the release with `?marketplace=true`, for example:  
     `https://github.com/GuyErreich/Action-Semver-Control/releases/edit/X.Y.Z?marketplace=true`
   - Or open the [Marketplace listing](https://github.com/marketplace/actions/new) / existing listing and publish from the new release tag.
4. Confirm `action.yml` includes `branding.icon` and `branding.color`.

Consumers should pin caller workflows at `@v1`. Exact semver pins (`@1.3.14`) and SHA pins remain supported via the reusable workflow `action-ref` input.
