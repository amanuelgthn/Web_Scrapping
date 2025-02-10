#!/usr/bin/env python3

import pandas as pd

# Load all sheets
all_sheets = pd.read_excel('resultsusa.xlsx', sheet_name=None)

# Print column names for each sheet to check if 'title' exists
for state, df in all_sheets.items():
    print(f"Sheet: {state}, Columns: {df.columns.tolist()}")
