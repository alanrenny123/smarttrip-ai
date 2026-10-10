"""
SmartTrip AI — Preprocessing Pipeline
Reusable pipeline for training and prediction.
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import os
import json
import joblib

# Column name mapping from raw dataset to normalized names
RAW_TO_NORM = {
    'Date': 'date',
    'Time': 'time',
    'Place': 'place',
    'Crowd_Count (in Thousands)': 'crowd_count',
    'Weather': 'weather',
    'Day_of_Week': 'day_of_week',
    'Holiday': 'holiday',
    'Event': 'event',
    'Temperature (°C)': 'temperature',
    'Week_of_Year': 'week_of_year',
    'Special_Features': 'special_features',
    'Region': 'region',
    'Transportation_Type': 'transportation_type',
}

# Features used for ML prediction
FEATURE_COLUMNS = [
    'place_encoded', 'hour', 'minute', 'day_of_week_encoded',
    'week_of_year', 'month', 'is_weekend', 'holiday_encoded',
    'event_encoded', 'weather_encoded', 'temperature',
    'region_encoded', 'transportation_encoded'
]

TARGET_COLUMN = 'crowd_count'

# Categorical columns and their encoding order
CATEGORICAL_COLUMNS = {
    'place': None,
    'day_of_week': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    'holiday': ['No', 'Yes'],
    'event': ['Regular Day', 'Cultural Event', 'Festival', 'National Holiday'],
    'weather': ['Clear', 'Sunny', 'Cloudy', 'Rainy'],
    'region': ['North', 'South', 'East', 'West', 'Central'],
    'transportation_type': ['Walking', 'Public', 'Private'],
}

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')


def load_dataset(path=None):
    """Load and normalize the raw Excel dataset."""
    if path is None:
        path = os.path.join(DATA_DIR, 'dataset.xlsx')

    df = pd.read_excel(path)

    # Normalize column names - handle encoding issues with degree symbol
    rename_map = {}
    for raw_col in df.columns:
        for key, val in RAW_TO_NORM.items():
            # Handle encoding issues with Temperature column
            if key.lower().replace('°', '').replace('c', '').strip() in raw_col.lower().replace('°', '').replace('c', '').strip() or key == raw_col:
                rename_map[raw_col] = val
                break
        if raw_col not in rename_map:
            # Fuzzy match for temperature column
            if 'temperature' in raw_col.lower() or 'temp' in raw_col.lower():
                rename_map[raw_col] = 'temperature'
            elif raw_col not in rename_map:
                rename_map[raw_col] = raw_col.lower().replace(' ', '_')

    df = df.rename(columns=rename_map)
    return df


def clean_dataset(df):
    """Clean and validate the dataset."""
    df = df.copy()

    # Parse date
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Parse time - handle string format
    def parse_time(t):
        if pd.isna(t):
            return 12, 0  # Default to noon
        t_str = str(t)
        try:
            parts = t_str.split(':')
            return int(parts[0]), int(parts[1])
        except:
            return 12, 0

    time_parsed = df['time'].apply(parse_time)
    df['hour'] = time_parsed.apply(lambda x: x[0])
    df['minute'] = time_parsed.apply(lambda x: x[1])

    # Ensure crowd_count is numeric
    df['crowd_count'] = pd.to_numeric(df['crowd_count'], errors='coerce')

    # Fill missing special_features
    df['special_features'] = df['special_features'].fillna('None')

    # Fill missing temperature with median
    if df['temperature'].isnull().any():
        df['temperature'] = df['temperature'].fillna(df['temperature'].median())

    return df


def engineer_features(df):
    """Create derived features for ML."""
    df = df.copy()

    # Month from date
    if 'date' in df.columns and not df['date'].isnull().all():
        df['month'] = df['date'].dt.month
    else:
        df['month'] = 1

    # Is weekend
    if 'day_of_week' in df.columns:
        df['is_weekend'] = df['day_of_week'].isin(['Saturday', 'Sunday']).astype(int)
    else:
        df['is_weekend'] = 0

    return df


class PreprocessingPipeline:
    """Reusable preprocessing pipeline for training and prediction."""

    def __init__(self):
        self.encoders = {}
        self.feature_columns = FEATURE_COLUMNS
        self.is_fitted = False
        self.places = []
        self.crowd_thresholds = {'low': 0, 'high': 0}

    def fit(self, df):
        """Fit encoders on training data."""
        df = clean_dataset(df)
        df = engineer_features(df)

        # Store unique places
        self.places = sorted(df['place'].unique().tolist())

        # Calculate crowd thresholds from data distribution
        q33 = df['crowd_count'].quantile(0.33)
        q66 = df['crowd_count'].quantile(0.66)
        self.crowd_thresholds = {
            'low': float(q33),
            'high': float(q66),
        }

        # Fit label encoders
        for col, categories in CATEGORICAL_COLUMNS.items():
            le = LabelEncoder()
            if categories is not None:
                le.fit(categories)
            else:
                le.fit(df[col].astype(str))
            self.encoders[col] = le

        self.is_fitted = True
        return self

    def transform(self, df, for_training=True):
        """Transform data using fitted encoders."""
        if not self.is_fitted:
            raise ValueError("Pipeline not fitted. Call fit() first.")

        df = clean_dataset(df)
        df = engineer_features(df)

        # Encode categorical columns
        for col, le in self.encoders.items():
            col_name = col + '_encoded'
            if col == 'transportation_type':
                col_name = 'transportation_encoded'

            if col in df.columns:
                # Handle unseen labels gracefully
                def safe_encode(val, encoder):
                    val_str = str(val)
                    if val_str in encoder.classes_:
                        return encoder.transform([val_str])[0]
                    return 0  # Default encoding for unknown values

                df[col_name] = df[col].apply(lambda x: safe_encode(x, le))
            else:
                df[col_name] = 0

        if for_training:
            return df[self.feature_columns + [TARGET_COLUMN]]
        else:
            return df[self.feature_columns]

    def fit_transform(self, df):
        """Fit and transform in one step."""
        self.fit(df)
        return self.transform(df, for_training=True)

    def classify_crowd(self, crowd_count):
        """Classify crowd count into LOW/MEDIUM/HIGH."""
        if crowd_count <= self.crowd_thresholds['low']:
            return 'LOW'
        elif crowd_count <= self.crowd_thresholds['high']:
            return 'MEDIUM'
        else:
            return 'HIGH'

    def prepare_single_prediction(self, place, date_str, time_str,
                                   weather='Clear', temperature=29,
                                   holiday='No', event='Regular Day',
                                   transportation='Private', region=None):
        """Prepare a single prediction input."""
        from datetime import datetime

        dt = pd.to_datetime(date_str)
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_of_week = day_names[dt.weekday()]

        # Parse time
        if isinstance(time_str, str):
            parts = time_str.replace(' AM', '').replace(' PM', '').split(':')
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0

            # Handle AM/PM
            if 'PM' in time_str.upper() and hour != 12:
                hour += 12
            elif 'AM' in time_str.upper() and hour == 12:
                hour = 0
        else:
            hour = 12
            minute = 0

        week_of_year = dt.isocalendar()[1]
        month = dt.month
        is_weekend = 1 if day_of_week in ['Saturday', 'Sunday'] else 0

        # Auto-detect region if not provided
        if region is None:
            region = self._guess_region(place)

        data = {
            'place': [place],
            'date': [dt],
            'time': [f"{hour:02d}:{minute:02d}:00"],
            'weather': [weather],
            'day_of_week': [day_of_week],
            'holiday': [holiday],
            'event': [event],
            'temperature': [temperature],
            'week_of_year': [week_of_year],
            'region': [region],
            'transportation_type': [transportation],
            'special_features': ['None'],
            'crowd_count': [0],
        }

        df = pd.DataFrame(data)
        return self.transform(df, for_training=False)

    def _guess_region(self, place):
        """Guess region based on place name."""
        place_lower = place.lower()
        if 'delhi' in place_lower:
            return 'North'
        elif 'mumbai' in place_lower:
            return 'West'
        elif 'hyderabad' in place_lower:
            return 'South'
        elif 'agra' in place_lower:
            return 'North'
        elif 'varanasi' in place_lower:
            return 'East'
        elif 'madhya pradesh' in place_lower:
            return 'Central'
        return 'North'  # Default

    def save(self, path=None):
        """Save the pipeline to disk."""
        if path is None:
            path = os.path.join(MODELS_DIR, 'preprocessing.pkl')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(path=None):
        """Load a saved pipeline from disk."""
        if path is None:
            path = os.path.join(MODELS_DIR, 'preprocessing.pkl')
        return joblib.load(path)
