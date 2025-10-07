"""
Version utilities for retrieving git version information.

This module provides utilities for getting version information from git,
with appropriate error handling and fallbacks.

Note: The get_git_version() function automatically increments the patch version
by 1 from the latest git tag using semantic versioning. This provides a
"next version" display for development builds.

Version parsing requires the python-semver package.
"""

import logging
from pathlib import Path
from typing import Optional
from git import Repo, InvalidGitRepositoryError, GitCommandError
import semver

logger = logging.getLogger(__name__)


def _increment_patch_version(version_tag: str) -> str:
    """Increment the patch version of a semver tag by 1.

    Uses python-semver package to parse and increment versions. Handles incomplete
    versions like "v1.2" by normalizing to "v1.2.0" before incrementing.

    Args:
        version_tag: Version tag string (e.g., "v1.2.3" or "1.2.3")

    Returns:
        New version tag with patch incremented by 1 (e.g., "v1.2.4")
    """
    try:
        # Preserve the 'v' prefix if it was present in the original
        has_v_prefix = version_tag.startswith("v")
        clean_version = version_tag.lstrip("v")

        # Handle incomplete versions by normalizing them first
        # Convert "1.2" to "1.2.0" for proper semver parsing
        version_parts = clean_version.split(".")
        if len(version_parts) == 2:
            clean_version = f"{clean_version}.0"
        elif len(version_parts) == 1:
            clean_version = f"{clean_version}.0.0"

        # Parse and validate the version using python-semver
        parsed_version = semver.Version.parse(clean_version)

        # Increment the patch version
        incremented_version = parsed_version.bump_patch()

        # Return with original prefix
        prefix = "v" if has_v_prefix else ""
        return f"{prefix}{incremented_version}"

    except (ValueError, semver.VersionError) as e:
        # If we can't parse it as semver, return the original
        logger.debug(f"Could not parse version as semver: {version_tag}, error: {e}")
        return version_tag


def get_git_version(repo_path: Optional[str] = None) -> str:
    """Get the latest git tag version with patch incremented by 1.

    This function attempts to retrieve the latest git tag using GitPython,
    finds the most recent tag by commit date, and automatically increments
    the patch version by 1 using semantic versioning.

    Args:
        repo_path: Path to git repository. If None, uses current directory.

    Returns:
        Git tag version string with patch incremented by 1, or 'unknown' if not available

    Examples:
        >>> version = get_git_version()  # Latest tag is "v2.7.4"
        >>> print(version)  # Outputs "v2.7.5"

        >>> version = get_git_version()  # Latest tag is "v1.5.0"
        >>> print(version)  # Outputs "v1.5.1"
    """
    try:
        # Use current directory if no path specified
        if repo_path is None:
            repo_path = Path.cwd()

        # Find the git repository (searches upwards from the given path)
        repo = Repo(repo_path, search_parent_directories=True)

        # Get all tags
        tags = list(repo.tags)

        if not tags:
            logger.debug("No git tags found in repository")
            return "unknown"

        # Sort tags by the commit date they reference (most recent last)
        try:
            sorted_tags = sorted(tags, key=lambda t: t.commit.committed_datetime)
            latest_tag = sorted_tags[-1]

            # Return the tag name with patch incremented by 1
            tag_name = str(latest_tag)
            incremented_version = _increment_patch_version(tag_name)
            logger.debug(
                f"Found latest git tag: {tag_name}, incremented to: {incremented_version}"
            )
            return incremented_version

        except Exception as e:
            logger.debug(f"Error sorting tags by commit date: {e}")
            # Fallback: just use the last tag alphabetically
            latest_tag = sorted(tags, key=str)[-1]
            tag_name = str(latest_tag)
            incremented_version = _increment_patch_version(tag_name)
            logger.debug(
                f"Using alphabetically last tag as fallback: {tag_name}, incremented to: {incremented_version}"
            )
            return incremented_version

    except InvalidGitRepositoryError:
        logger.debug("Not in a git repository")
        return "unknown"
    except GitCommandError as e:
        logger.debug(f"Git command error: {e}")
        return "unknown"
    except Exception as e:
        logger.debug(f"Unexpected error getting git version: {e}")
        return "unknown"


def get_git_describe(repo_path: Optional[str] = None) -> str:
    """Get git describe output for the latest tag.

    Args:
        repo_path: Path to git repository. If None, uses current directory.

    Returns:
        Git describe output, or 'unknown' if not available
    """
    try:
        # Use current directory if no path specified
        if repo_path is None:
            repo_path = Path.cwd()

        repo = Repo(repo_path, search_parent_directories=True)

        # Get all tags
        tags = list(repo.tags)
        if not tags:
            return "unknown"

        # Sort tags by commit date and get the latest
        sorted_tags = sorted(tags, key=lambda t: t.commit.committed_datetime)
        latest_tag = sorted_tags[-1]

        # Get describe output for the latest tag
        describe_output = repo.git.describe("--tags", str(latest_tag))
        logger.debug(f"Git describe output: {describe_output}")
        return describe_output

    except Exception as e:
        logger.debug(f"Error getting git describe: {e}")
        return "unknown"


def get_version_info(repo_path: Optional[str] = None) -> dict:
    """Get comprehensive version information.

    Args:
        repo_path: Path to git repository. If None, uses current directory.

    Returns:
        Dictionary containing version information including:
        - git_version: Git tag version with patch incremented by 1
        - git_available: Whether git is available
        - git_describe: Git describe output
        - package_version: Package version from __init__.py if available
    """
    git_version = get_git_version(repo_path)
    git_available = git_version != "unknown"
    git_describe = get_git_describe(repo_path) if git_available else "unknown"

    # Try to get package version
    package_version = "unknown"
    try:
        from .. import __version__

        package_version = __version__
    except (ImportError, AttributeError):
        pass

    return {
        "git_version": git_version,
        "git_available": git_available,
        "git_describe": git_describe,
        "package_version": package_version,
    }
