import logging
import re

from src.version import Version

logger = logging.getLogger(__name__)

def update_version_in_file(file_path: str, new_version_obj: Version) -> None:
    """
    Update only the version segment in version lines, preserving title/prefix,
    by merging from the new_version_obj and reformatting.
    """
    try:
        with open(file_path, 'r+') as f:
            lines = f.readlines()
            updated_lines = []

            for line in lines:
                try:
                    current = Version.parse(line)
                    current.merge_from(new_version_obj)
                    updated_line = current.format_full_line()
                    logger.debug(f"Updated: {line.strip()} -> {updated_line.strip()}")
                    updated_lines.append(updated_line + "\n")
                except ValueError:
                    updated_lines.append(line)

            f.seek(0)
            f.writelines(updated_lines)
            f.truncate()

            logger.info(f"Updated version in {file_path} to {str(new_version_obj)}")
    except FileNotFoundError:
        logger.warning(f"File not found: {file_path}. Skipping.")
    except Exception as e:
        logger.error(f"Failed to update version in {file_path}: {e}")
        raise