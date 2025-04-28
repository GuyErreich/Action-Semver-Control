import logging
import re

from src.version import Version

logger = logging.getLogger(__name__)

def update_version_in_file(file_path: str, new_version_obj: Version) -> None:
    try:
        with open(file_path, 'r+') as f:
            content = f.read()

            def replacer(match: re.Match) -> str:
                old_line = match.group(0)
                logger.debug(f"Replacing old version line: {old_line} -> {str(new_version_obj)}")
                return str(new_version_obj)

            new_content = Version.version_pattern.sub(replacer, content)

            f.seek(0)
            f.write(new_content)
            f.truncate()

            logger.info(f"Updated version in {file_path} to {str(new_version_obj)}")

    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}. Skipping.")
    except Exception as e:
        logger.error(f"Failed to update version in {file_path}: {e}")
        raise