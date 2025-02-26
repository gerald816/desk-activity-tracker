import pandas as pd
from datetime import datetime
import pytz

def calculate_health_score(standing_minutes: float) -> tuple:
    """Calculate health score based on Health Canada recommendations."""
    min_recommended = 120  # 2 hours in minutes
    max_recommended = 240  # 4 hours in minutes

    if standing_minutes < min_recommended:
        score = (standing_minutes / min_recommended) * 100
        message = "Try to stand more to meet the minimum recommendation of 2 hours"
    elif min_recommended <= standing_minutes <= max_recommended:
        score = 100
        message = "Great job! You're within the recommended standing time"
    else:
        score = 100 - ((standing_minutes - max_recommended) / max_recommended * 20)
        message = "Consider reducing standing time to stay within recommendations"

    return max(min(score, 100), 0), message

def load_activity_data() -> pd.DataFrame:
    """Load activity data from CSV file."""
    try:
        df = pd.read_csv('activity_data.csv')
        # Handle timestamp parsing with UTC awareness
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
        # Drop any rows with invalid timestamps
        df = df.dropna(subset=['timestamp'])
        return df
    except FileNotFoundError:
        # Create empty DataFrame with correct columns and types
        df = pd.DataFrame(columns=['timestamp', 'activity', 'duration_minutes'])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df

def save_activity_data(df: pd.DataFrame):
    """Save activity data to CSV file."""
    df.to_csv('activity_data.csv', index=False)

def validate_time_input(start_time: datetime, end_time: datetime) -> tuple:
    """Validate time input for manual entries."""
    if not start_time or not end_time:
        return False, "Please provide both start and end times"

    if end_time <= start_time:
        return False, "End time must be after start time"

    # Only check if the end time is beyond today
    if end_time.date() > datetime.now(pytz.UTC).date():
        return False, "End time cannot be in the future"

    duration = (end_time - start_time).total_seconds() / 60
    if duration > 24 * 60:  # More than 24 hours
        return False, "Duration cannot exceed 24 hours"

    return True, ""