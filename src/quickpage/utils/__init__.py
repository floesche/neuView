"""
Utility modules for QuickPage.

This package contains utility functions and formatters that were extracted
from the main PageGenerator class to improve code organization and reusability.
"""

from .formatters import NumberFormatter, PercentageFormatter, SynapseFormatter, NeurotransmitterFormatter
from .html_utils import HTMLUtils
from .text_utils import TextUtils
from ..visualization.color import ColorUtils

__all__ = [
    'NumberFormatter',
    'PercentageFormatter',
    'SynapseFormatter',
    'NeurotransmitterFormatter',
    'HTMLUtils',
    'ColorUtils',
    'TextUtils'
]
