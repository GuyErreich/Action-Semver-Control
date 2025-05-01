from typing import List
import logging

logger = logging.getLogger(__name__)

def update_changelog(new_version: str, commit_messages: List[str]) -> None:
    logging.info(f"Updating changelog for version: {new_version}")
    entry = f"\n## {new_version}\n"
    if commit_messages:
        logging.info("Adding commit messages to changelog entry.")
        for msg in commit_messages:
            entry += f"- {msg}\n"
    else:
        logging.info("No commit messages provided. Adding default message.")
        entry += "- No notable changes.\n"

    try:
        with open('CHANGELOG.md', 'r+') as f:
            logging.info("Reading existing CHANGELOG.md file.")
            content = f.read()
            f.seek(0, 0)
            logging.info("Writing new changelog entry at the top of the file.")
            f.write(entry + content)
    except FileNotFoundError:
        logging.warning("CHANGELOG.md not found. Creating a new file.")
        with open('CHANGELOG.md', 'w') as f:
            logging.info("Writing new changelog entry to the new file.")
            f.write(f"# Changelog\n{entry}")
