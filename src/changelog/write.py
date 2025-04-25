import datetime
import logging
import os

logger = logging.getLogger("semver-action")


def prepend_changelog(version, branch, changelog_file):
    logger.debug(f"Updating changelog {changelog_file}")

    date = datetime.date.today().isoformat()
    entry = f"## {version} - {date}\n\n- Merged from `{branch}`\n\n"

    if os.path.exists(changelog_file):
        with open(changelog_file) as f:
            content = f.read().lstrip("\n")  # Strip leading newlines only
    else:
        content = ""

    with open(changelog_file, "w") as f:
        f.write(entry + content)

    logger.debug("Changelog updated")
