# Changelog
All notable changes to this project will be documented in this file.

## [1.8.6-dev] - 10-10-2026

### ✨ Features & Enhancements
- sync package locks after version bumps (#306)
- run auto-semver from the installed package (#339)
### 🔧 Infrastructure & Tooling
- freeze Docker and CI installs to uv.lock (#305)
- digest-pin skywalking-eyes and document nested SHA policy (#304)
- bump astral-sh/setup-uv from 10.1.0 to 10.2.0 in the github-actions group across 1 directory (#323)
- bump the uv group with 6 updates (#330)
### 🐛 Bug Fixes & Resolutions
- delete source-removed paths on signed promote (#328)
- use absolute wtp base_dir (no tilde expansion) (#307)
- align CI and action uv so release bumps refresh uv.lock (#337)
- pin the action install to auto-semver-control (#340)

## License
This project is licensed under the MIT License.