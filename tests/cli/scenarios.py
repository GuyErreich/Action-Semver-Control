from typing import Literal

from tests.helpers.fake_repo_scenerio import FakeGitScenario

type SCENARIOS_TYPE = Literal['basic-bump', 'missing-version-file', 'no-semver-lock']
SCENARIOS: dict[SCENARIOS_TYPE, FakeGitScenario] = {}

START_VERSION = "1.2.3"
BUMPED_VERSION = "1.2.4"

PULL_REQUEST_INFO = {
    "title": f"Release {START_VERSION}",
    "body": f"Automated release for {START_VERSION}.",
    "labels": ["semver"],
    "merged": True,
    "merge_commit_sha": "abc123"
}

# Shared changelog template
CHANGELOG_INFO = {
    "path": "CHANGELOG.md",
    "prepend": True,
    "template": "## {{version}} - {{date}}\\n- {{message}}"
}

def generate_expected(version: str) -> dict[str, str]:
    return {
        "version.txt": version,
        ".semver.lock": version,
        "CHANGELOG.md": version
    }


# Basic bump scenario
SCENARIOS["basic-bump"] = FakeGitScenario(
    template_data={
        "start_version": START_VERSION,
        "suffixes": {"dev": "-dev", "main": ""},
        "promotions": {"dev": "main"},
        "version_files": ["version.txt"],
        "pull_request": PULL_REQUEST_INFO,
        "changelog": CHANGELOG_INFO,
        "version": START_VERSION,
        "source_branch": "dev",
        "target_branch": "main",
        "repository": "user/repo"
    },
    expected={
        "version": BUMPED_VERSION,
        "files": generate_expected(BUMPED_VERSION)
    },
    use_templates=[
        "auto_semver_config.yml",
        "version.txt",
        ".semver.lock",
        ".github/event.json"
    ],
    branches={
        "dev": ["abc123"],
        "main": ["abc122"]
    },
    tags={
        "v1.2.3": "abc122"
    },
    remotes={
        "origin": {
            "dev": ["abc123"],
            "main": ["abc122"]
        }
    }
)

# Scenario without version.txt
SCENARIOS["missing-version-file"] = FakeGitScenario(
    template_data={
        **SCENARIOS["basic-bump"].template_data
    },
    expected={
        "version": BUMPED_VERSION,
        "files": generate_expected(BUMPED_VERSION)
    },
    use_templates=[
        "auto_semver_config.yml",
        ".semver.lock",
        ".github/event.json"
    ],
    branches={
        "dev": ["abc123"],
        "main": ["abc122"]
    }
)

# Scenario without semver.lock
SCENARIOS["no-semver-lock"] = FakeGitScenario(
    template_data={
        **SCENARIOS["basic-bump"].template_data
    },
    expected={
        "version": BUMPED_VERSION,
        "files": generate_expected(BUMPED_VERSION)
    },
    use_templates=[
        "auto_semver_config.yml",
        "version.txt",
        ".github/event.json"
    ],
    branches={
        "dev": ["abc123"],
        "main": ["abc122"]
    }
)
