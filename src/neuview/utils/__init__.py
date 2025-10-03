"""
Utility modules for neuView.

This package contains utility functions and formatters that were extracted
from the main PageGenerator class to improve code organization and reusability.
"""

from .formatters import (
    NumberFormatter,
    PercentageFormatter,
    SynapseFormatter,
    NeurotransmitterFormatter,
    MathematicalFormatter,
)
from .html_utils import HTMLUtils
from .text_utils import TextUtils
from .version_utils import get_git_version, get_git_describe, get_version_info


__all__ = [
    "NumberFormatter",
    "PercentageFormatter",
    "SynapseFormatter",
    "NeurotransmitterFormatter",
    "MathematicalFormatter",
    "HTMLUtils",
    "TextUtils",
    "get_git_version",
    "get_git_describe",
    "get_version_info",
]
