"""Phase 1: Data Inspection Script for SmartTrip AI"""
import pandas as pd
import numpy as np
import json

# Load dataset
DATASET_PATH = r"DOC-20260902-WA0065 (1).xlsx"

print("=" * 70)
print("PHASE 1: DATASET INSPECTION")
print("=" * 70)

try:
    df = pd.read_excel(DATASET_PATH)
except Exception as e:
    print(f"Error loading Excel: {e}")
    exit(1)

# 1. Shape
print(f"\n1. DATASET SHAPE: {df.shape}")
print(f"   Rows: {df.shape[0]}, Columns: {df.shape[1]}")

# 2. Exact Column Names
print(f"\n2. EXACT COLUMN NAMES:")
for i, col in enumerate(df.columns):
    print(f"   [{i}] '{col}' (dtype: {df[col].dtype})")

# 3. First 10 Rows
print(f"\n3. FIRST 10 ROWS:")
print(df.head(10).to_string())

# 4. Basic Statistics
print(f"\n4. BASIC STATISTICS:")
print(df.describe(include='all').to_string())

# 5. Missing Values
print(f"\n5. MISSING VALUES:")
missing = df.isnull().sum()
for col in df.columns:
    print(f"   {col}: {missing[col]} ({missing[col]/len(df)*100:.1f}%)")

# 6. Duplicate Rows
dupes = df.duplicated().sum()
print(f"\n6. DUPLICATE ROWS: {dupes}")

# 7. Unique Destinations
place_cols = [c for c in df.columns if 'place' in c.lower() or 'destination' in c.lower() or 'location' in c.lower()]
print(f"\n7. POTENTIAL PLACE/DESTINATION COLUMNS: {place_cols}")
for col in place_cols:
    unique_vals = df[col].unique()
    print(f"   '{col}' unique values ({len(unique_vals)}):")
    for v in sorted(unique_vals, key=str):
        print(f"      - {v}")

# 8. Date Range
date_cols = [c for c in df.columns if 'date' in c.lower()]
print(f"\n8. DATE COLUMNS: {date_cols}")
for col in date_cols:
    try:
        dates = pd.to_datetime(df[col], errors='coerce')
        print(f"   '{col}': {dates.min()} to {dates.max()}")
    except:
        print(f"   '{col}': Could not parse as dates")

# 9. Weather Values
weather_cols = [c for c in df.columns if 'weather' in c.lower()]
print(f"\n9. WEATHER COLUMNS: {weather_cols}")
for col in weather_cols:
    print(f"   '{col}' unique values: {df[col].unique().tolist()}")

# 10. Crowd Statistics
crowd_cols = [c for c in df.columns if 'crowd' in c.lower()]
print(f"\n10. CROWD COLUMNS: {crowd_cols}")
for col in crowd_cols:
    if pd.api.types.is_numeric_dtype(df[col]):
        print(f"   '{col}' stats:")
        print(f"      Min: {df[col].min()}")
        print(f"      Max: {df[col].max()}")
        print(f"      Mean: {df[col].mean():.1f}")
        print(f"      Median: {df[col].median():.1f}")
        print(f"      Std: {df[col].std():.1f}")
        q33 = df[col].quantile(0.33)
        q66 = df[col].quantile(0.66)
        print(f"      33rd percentile: {q33:.0f}")
        print(f"      66th percentile: {q66:.0f}")
    else:
        print(f"   '{col}' unique values: {df[col].unique().tolist()}")

# 11. Time column
time_cols = [c for c in df.columns if 'time' in c.lower() or 'hour' in c.lower()]
print(f"\n11. TIME COLUMNS: {time_cols}")
for col in time_cols:
    print(f"   '{col}' sample values: {df[col].head(10).tolist()}")
    print(f"   dtype: {df[col].dtype}")
    print(f"   unique count: {df[col].nunique()}")

# 12. Categorical columns
print(f"\n12. CATEGORICAL VS NUMERICAL:")
for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]):
        print(f"   NUMERICAL: '{col}' (unique: {df[col].nunique()})")
    else:
        print(f"   CATEGORICAL: '{col}' (unique: {df[col].nunique()})")

# 13. All unique values for low-cardinality categorical columns
print(f"\n13. UNIQUE VALUES FOR CATEGORICAL COLUMNS:")
for col in df.columns:
    if not pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique() <= 30:
        print(f"   '{col}': {sorted(df[col].dropna().unique().tolist(), key=str)}")

# 14. Region
region_cols = [c for c in df.columns if 'region' in c.lower()]
print(f"\n14. REGION COLUMNS: {region_cols}")
for col in region_cols:
    print(f"   '{col}' unique: {df[col].unique().tolist()}")

# 15. Transportation
transport_cols = [c for c in df.columns if 'transport' in c.lower()]
print(f"\n15. TRANSPORTATION COLUMNS: {transport_cols}")
for col in transport_cols:
    print(f"   '{col}' unique: {df[col].unique().tolist()}")

# 16. Holiday/Event
holiday_cols = [c for c in df.columns if 'holiday' in c.lower() or 'event' in c.lower()]
print(f"\n16. HOLIDAY/EVENT COLUMNS: {holiday_cols}")
for col in holiday_cols:
    print(f"   '{col}' unique: {df[col].unique().tolist()}")

# 17. Special features
special_cols = [c for c in df.columns if 'special' in c.lower() or 'feature' in c.lower()]
print(f"\n17. SPECIAL FEATURE COLUMNS: {special_cols}")
for col in special_cols:
    print(f"   '{col}' unique: {df[col].unique().tolist()}")

# 18. Temperature
temp_cols = [c for c in df.columns if 'temp' in c.lower()]
print(f"\n18. TEMPERATURE COLUMNS: {temp_cols}")
for col in temp_cols:
    if pd.api.types.is_numeric_dtype(df[col]):
        print(f"   '{col}': min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.1f}")

# 19. Check for lat/lon/distance columns
geo_cols = [c for c in df.columns if any(g in c.lower() for g in ['lat', 'lon', 'distance', 'coord'])]
print(f"\n19. GEOGRAPHIC COLUMNS: {geo_cols if geo_cols else 'NONE FOUND'}")

print("\n" + "=" * 70)
print("END OF PHASE 1 INSPECTION")
print("=" * 70)
