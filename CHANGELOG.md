# Changelog
All notable changes to this project will be documented in this file.

## [1.8.4-dev] - 08-10-2026

### ✨ Features & Enhancements
- sync package locks after version bumps (#306)
### 🔧 Infrastructure & Tooling
- freeze Docker and CI installs to uv.lock (#305)
- digest-pin skywalking-eyes and document nested SHA policy (#304)
- bump astral-sh/setup-uv from 10.1.0 to 10.2.0 in the github-actions group across 1 directory (#323)
### 🐛 Bug Fixes & Resolutions
- delete source-removed paths on signed promote (#328)
- use absolute wtp base_dir (no tilde expansion) (#307)

## License
This project is licensed under the MIT License.