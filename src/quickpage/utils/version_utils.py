"""
Version utilities for retrieving git version information.

This module provides utilities for getting version information from git,
with appropriate error handling and fallbacks.
"""

import logging
from pathlib import Path
from typing import Optional
from git import Repo, InvalidGitRepositoryError, GitCommandError

logger = logging.getLogger(__name__)


def get_git_version(repo_path: Optional[str] = None) -> str:
    """Get the latest git tag version.

    This function attempts to retrieve the latest git tag using GitPython.
    It finds the most recent tag by commit date.

    Args:
        repo_path: Path to git repository. If None, uses current directory.

    Returns:
        Git tag version string, or 'unknown' if not available

    Examples:
        >>> version = get_git_version()
        >>> print(version)  # e.g., "v2.6" or "unknown"
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

            # Return the tag name (remove 'refs/tags/' prefix if present)
            tag_name = str(latest_tag)
            logger.debug(f"Found latest git tag: {tag_name}")
            return tag_name

        except Exception as e:
            logger.debug(f"Error sorting tags by commit date: {e}")
            # Fallback: just use the last tag alphabetically
            latest_tag = sorted(tags, key=str)[-1]
            tag_name = str(latest_tag)
            logger.debug(f"Using alphabetically last tag as fallback: {tag_name}")
            return tag_name

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
        - git_version: Git tag version
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
