#!/usr/bin/env python3
"""
Test empty DataFrame handling.
"""

import sys
from pathlib import Path
import pandas as pd

# Add the src directory to the path so we can import quickpage
sys.path.insert(0, str(Path(__file__).parent / "src"))

from quickpage import Config, NeuPrintConnector

config = Config.load('config.yaml')
connector = NeuPrintConnector(config)

# Create empty DataFrame to simulate no results
empty_df = pd.DataFrame()
print("Testing empty DataFrame...")
summary = connector._calculate_summary(empty_df, 'LC10', 'both')
print('Empty DF summary:', summary)
