"""
Project path utilities using pyprojroot to locate the project root.
"""

from pathlib import Path
from pyprojroot import here


def get_project_root() -> Path:
    """
    Get the project root directory (where pyproject.toml is located).

    Returns:
        Path: The project root directory

    Raises:
        RuntimeError: If pyproject.toml cannot be found
    """
    try:
        return here()
    except Exception as e:
        raise RuntimeError(f"Could not locate project root (pyproject.toml): {e}")


def get_templates_dir() -> Path:
    """
    Get the templates directory path.

    Returns:
        Path: The templates directory path
    """
    return get_project_root() / "templates"


def get_static_dir() -> Path:
    """
    Get the static directory path.

    Returns:
        Path: The static directory path
    """
    return get_project_root() / "static"


def get_input_dir() -> Path:
    """
    Get the input directory path.

    Returns:
        Path: The input directory path
    """
    return get_project_root() / "input"


def get_src_dir() -> Path:
    """
    Get the src directory path.

    Returns:
        Path: The src directory path
    """
    return get_project_root() / "src"
