#!/usr/bin/env python3
"""
Auto-increment version script for quickpage project.

This script runs after the 'create-all-pages' pixi task succeeds.
It reads the current version from git tags, increments the patch version,
and creates a new git tag.
"""

import subprocess
import sys
import re
import argparse
from typing import Optional, Tuple


def run_command(cmd: list[str]) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return 1, "", str(e)


def get_latest_version() -> Optional[str]:
    """Get the latest version tag from git."""
    # Get all tags and sort them by version
    exit_code, stdout, stderr = run_command(
        ["git", "tag", "--list", "--sort=-version:refname"]
    )

    if exit_code != 0:
        print(f"Error getting git tags: {stderr}", file=sys.stderr)
        return None

    if not stdout:
        print("No git tags found", file=sys.stderr)
        return None

    tags = stdout.split("\n")

    # Find the first tag that matches semantic versioning pattern
    semver_pattern = re.compile(r"^v?(\d+)\.(\d+)(?:\.(\d+))?$")

    for tag in tags:
        if semver_pattern.match(tag):
            return tag

    print("No valid semantic version tags found", file=sys.stderr)
    return None


def parse_version(version_tag: str) -> Tuple[int, int, int]:
    """Parse a version tag into major, minor, patch components."""
    # Remove 'v' prefix if present
    version = version_tag.lstrip("v")

    semver_pattern = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?$")
    match = semver_pattern.match(version)

    if not match:
        raise ValueError(f"Invalid version format: {version_tag}")

    major = int(match.group(1))
    minor = int(match.group(2))
    patch = int(match.group(3)) if match.group(3) else 0

    return major, minor, patch


def increment_patch_version(major: int, minor: int, patch: int) -> str:
    """Increment the patch version."""
    return f"v{major}.{minor}.{patch + 1}"


def create_git_tag(tag: str, dry_run: bool = False) -> bool:
    """Create a new git tag."""
    # First check if the tag already exists
    exit_code, stdout, stderr = run_command(["git", "tag", "--list", tag])
    if exit_code != 0:
        print(f"Error checking existing tags: {stderr}", file=sys.stderr)
        return False

    if stdout:
        print(f"Tag {tag} already exists, skipping creation", file=sys.stderr)
        return False

    # Check if we have any uncommitted changes
    exit_code, stdout, stderr = run_command(["git", "status", "--porcelain"])
    if exit_code != 0:
        print(f"Error checking git status: {stderr}", file=sys.stderr)
        return False

    if stdout:
        print(
            "Warning: There are uncommitted changes in the repository", file=sys.stderr
        )
        print("Staged/modified files:", file=sys.stderr)
        print(stdout, file=sys.stderr)
        # Continue anyway as the user might want to tag the current state

    # Create the tag
    if dry_run:
        print(f"[DRY RUN] Would create git tag: {tag}")
        return True

    exit_code, stdout, stderr = run_command(
        [
            "git",
            "tag",
            "-a",
            tag,
            "-m",
            f"Auto-increment patch to {tag} after successful create-all-pages",
        ]
    )

    if exit_code != 0:
        print(f"Error creating git tag: {stderr}", file=sys.stderr)
        return False

    print(f"Successfully created git tag: {tag}")
    return True


def main():
    """Main function to increment version and create tag."""
    parser = argparse.ArgumentParser(description="Increment version and create git tag")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually creating the tag",
    )

    args = parser.parse_args()

    if args.dry_run:
        print("Starting version increment process (DRY RUN MODE)...")
    else:
        print("Starting version increment process...")

    # Get the latest version
    latest_version = get_latest_version()
    if not latest_version:
        print("Could not determine latest version", file=sys.stderr)
        sys.exit(1)

    print(f"Current latest version: {latest_version}")

    try:
        # Parse the version
        major, minor, patch = parse_version(latest_version)
        print(f"Parsed version: major={major}, minor={minor}, patch={patch}")

        # Increment patch version
        new_version = increment_patch_version(major, minor, patch)
        print(f"New version: {new_version}")

        # Create the git tag
        if create_git_tag(new_version, dry_run=args.dry_run):
            if args.dry_run:
                print(
                    f"[DRY RUN] Would increment version from {latest_version} to {new_version}"
                )
                print(f"[DRY RUN] To actually create the tag, run without --dry-run")
            else:
                print(
                    f"Version successfully incremented from {latest_version} to {new_version}"
                )

            # Optionally push the tag (commented out by default for safety)
            # print("To push the tag to remote, run: git push origin", new_version)
        else:
            print("Failed to create git tag", file=sys.stderr)
            sys.exit(1)

    except ValueError as e:
        print(f"Error parsing version: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
