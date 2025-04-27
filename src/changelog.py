from typing import List

def update_changelog(new_version: str, commit_messages: List[str]) -> None:
    entry = f"\n## {new_version}\n"
    if commit_messages:
        for msg in commit_messages:
            entry += f"- {msg}\n"
    else:
        entry += "- No notable changes.\n"

    try:
        with open('CHANGELOG.md', 'r+') as f:
            content = f.read()
            f.seek(0, 0)
            f.write(entry + content)
    except FileNotFoundError:
        with open('CHANGELOG.md', 'w') as f:
            f.write(f"# Changelog\n{entry}")
