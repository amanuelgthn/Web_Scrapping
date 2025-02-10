#!/usr/bin/env python3

import pandas as pd

# Load all sheets from the Excel file
all_sheets = pd.read_excel('resultsusa.xlsx', sheet_name=None)

# List to store cleaned data
frames = []

# Process each sheet
for state, df in all_sheets.items():
    print(f"Processing sheet: {state}, Columns: {df.columns.tolist()}")

    # Skip empty sheets
    if df.empty:
        print(f"Skipping {state} (empty sheet).")
        continue

    # Check if 'title' column exists
    if 'title' in df.columns:
        new_df = pd.DataFrame({
            'Company Name': df['title'],
            'Contact Name': '',  # No contact name provided
            'Email': df.get('email', ''),  # Use .get() to avoid KeyError
            'Job Position': '',
            'Mobile': df.get('phone', ''),
            'Website': df.get('website', ''),
            'LinkedIn': df.get('linkedin', ''),
            'State': state,  # Add the state name
            'City': ''  # City data is not available
        })
        frames.append(new_df)
    else:
        print(f"Skipping {state} (missing 'title' column).")

# Combine all processed data into one DataFrame
if frames:
    all_states_df = pd.concat(frames, ignore_index=True)

    # Save the cleaned data into a new Excel file
    with pd.ExcelWriter('organized_resultusa.xlsx') as writer:
        all_states_df.to_excel(writer, sheet_name='All states', index=False)

    print("The 'All states' sheet has been created successfully.")
else:
    print("No valid data found. Check your Excel sheets for missing 'title' columns.")
