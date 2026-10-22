import pandas as pd
from pandas import DateOffset

# Read the CSV file
print("Reading filtered_main_data.csv...")
df = pd.read_csv('filtered_main_data.csv')

# List of columns to extract
columns_to_extract = [
    'unique_id',
    'location_id',
    'timestamp',
    'y',
    'latitude',
    'longitude',
    'location',
    'cluster_size',
    'freq',
    'temperature_2m',
    'relative_humidity_2m',
    'apparent_temperature',
    'precipitation',
    'rain',
    'snowfall',
    'weather_code',
    'cloud_cover',
    'is_day',
    'sunshine_duration'
]

# Select the required columns
print("Selecting columns...")
df_selected = df[columns_to_extract].copy()

# Shift timestamp by 10 years
print("Shifting timestamp by 10 years...")
df_selected['timestamp'] = pd.to_datetime(df_selected['timestamp']) + DateOffset(years=10)

# Calculate consumption_per_building = y / cluster_size
print("Calculating consumption_per_building...")
df_selected['consumption_per_building'] = df_selected['y'] / df_selected['cluster_size']

# Reorder columns to have consumption_per_building after precipitation
cols = columns_to_extract[:13] + ['consumption_per_building'] + columns_to_extract[13:]
df_selected = df_selected[cols]

# Save to new CSV file
output_file = 'extracted_columns.csv'
print(f"Saving to {output_file}...")
df_selected.to_csv(output_file, index=False)

print(f"Done! Saved {len(df_selected)} rows with {len(df_selected.columns)} columns to {output_file}")
print(f"\nColumns saved: {list(df_selected.columns)}")
