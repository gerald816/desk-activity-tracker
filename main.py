import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta, time, date
from utils import calculate_health_score, load_activity_data, save_activity_data, validate_time_input
import pytz

# Page configuration
st.set_page_config(page_title="Desk Position Tracker",
                   page_icon="🪑",
                   layout="wide")

# Initialize session state
if 'standing' not in st.session_state:
    st.session_state.standing = False
if 'last_toggle' not in st.session_state:
    st.session_state.last_toggle = datetime.now(pytz.UTC)
if 'timezone' not in st.session_state:
    st.session_state.timezone = 'America/New_York'  # Default to EST
if 'editing_activity' not in st.session_state:
    st.session_state.editing_activity = None
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0
if 'activity_started' not in st.session_state:
    st.session_state.activity_started = False

# Sidebar for settings with clock icon
with st.sidebar:
    st.title("⏰ Time Settings")
    selected_timezone = st.selectbox("Select Timezone",
                                     options=pytz.common_timezones,
                                     index=pytz.common_timezones.index(
                                         st.session_state.timezone))
    if selected_timezone != st.session_state.timezone:
        st.session_state.timezone = selected_timezone
        st.rerun()

# Convert UTC times to local timezone
local_tz = pytz.timezone(st.session_state.timezone)
current_time = datetime.now(local_tz)

# Load data
df = load_activity_data()

# Add this after loading the data to enable automatic refresh every 30 seconds
st.session_state.refresh_counter = (st.session_state.refresh_counter + 1) % 30
if st.session_state.refresh_counter == 0:
    st.rerun()

# Get latest activity end time
latest_time = time(9, 0)  # Default to 9 AM
if not df.empty:
    latest_record = df.iloc[-1]
    latest_end_time = latest_record['timestamp'] + pd.Timedelta(
        minutes=latest_record['duration_minutes'])
    latest_time = latest_end_time.tz_convert(local_tz).time()

# Main title
st.title("📊 Desk Position Tracker")

# Current status and toggle section
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Current Status")

    if not st.session_state.activity_started:
        st.info(
            "No active tracking. Click 'Start Activity' to begin tracking your desk position."
        )
        if st.button("Start Activity"):
            st.session_state.activity_started = True
            st.session_state.last_toggle = current_time.astimezone(pytz.UTC)
            st.rerun()
    else:
        status_text = "🧍 Standing" if st.session_state.standing else "🪑 Sitting"
        st.subheader(status_text)

        # Calculate duration in current position
        duration = (current_time -
                    st.session_state.last_toggle.astimezone(local_tz))
        duration_minutes = duration.total_seconds() / 60

        # Display duration and recommendation with encouraging emojis
        st.markdown(
            f"**{status_text} since:** {st.session_state.last_toggle.astimezone(local_tz).strftime('%I:%M %p')}"
        )

        # Duration with encouraging messages for standing only
        duration_message = f"**Duration:** {int(duration_minutes)} minutes "
        if st.session_state.standing:
            if duration_minutes >= 60:
                duration_message += "🌟 Amazing effort! What great endurance!"
            elif duration_minutes >= 45:
                duration_message += "🎯 Great progress! Almost at your goal!"
            elif duration_minutes >= 30:
                duration_message += "💪 Halfway there! Keep it up!"
            elif duration_minutes >= 15:
                duration_message += "⭐ Good start! You're doing great!"
            else:
                duration_message += "🌱 Just getting started!"

        st.markdown(duration_message)

        # Time to switch recommendation
        if duration_minutes >= 60:  # Suggest switching after 60 minutes
            st.warning(
                f"⚠️ Consider switching positions! You've been {status_text.lower()} for over an hour."
            )
        else:
            minutes_left = 60 - int(duration_minutes)
            st.info(
                f"💡 Consider switching positions in {minutes_left} minutes")

        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Toggle Position"):
                current_time_utc = current_time.astimezone(pytz.UTC)
                duration = (current_time_utc -
                            st.session_state.last_toggle).total_seconds() / 60

                # Record the activity
                new_record = pd.DataFrame({
                    'timestamp': [st.session_state.last_toggle],
                    'activity':
                    ['standing' if st.session_state.standing else 'sitting'],
                    'duration_minutes': [duration]
                })
                df = pd.concat([df, new_record], ignore_index=True)
                save_activity_data(df)

                # Update state
                st.session_state.standing = not st.session_state.standing
                st.session_state.last_toggle = current_time_utc
                st.rerun()

        with col2:
            if st.button("End Activity"):
                current_time_utc = current_time.astimezone(pytz.UTC)
                duration = (current_time_utc -
                            st.session_state.last_toggle).total_seconds() / 60

                # Record the final activity
                new_record = pd.DataFrame({
                    'timestamp': [st.session_state.last_toggle],
                    'activity':
                    ['standing' if st.session_state.standing else 'sitting'],
                    'duration_minutes': [duration]
                })
                df = pd.concat([df, new_record], ignore_index=True)
                save_activity_data(df)

                st.session_state.standing = False
                st.session_state.activity_started = False
                st.session_state.last_toggle = current_time_utc
                st.success("✅ Activity ended!")
                st.rerun()

        with col3:
            if st.button("End Workday"):
                current_time_utc = current_time.astimezone(pytz.UTC)
                duration = (current_time_utc -
                            st.session_state.last_toggle).total_seconds() / 60

                # Record the final activity
                new_record = pd.DataFrame({
                    'timestamp': [st.session_state.last_toggle],
                    'activity':
                    ['standing' if st.session_state.standing else 'sitting'],
                    'duration_minutes': [duration]
                })
                df = pd.concat([df, new_record], ignore_index=True)
                save_activity_data(df)

                st.session_state.standing = False
                st.session_state.activity_started = False
                st.session_state.last_toggle = current_time_utc
                st.balloons()
                st.success("🎉 Great job today! See you tomorrow!")
                st.rerun()

        # Current activity editor
        if st.session_state.activity_started:
            with st.expander("Edit Current Activity"):
                new_start_time = st.time_input(
                    "Adjust Start Time",
                    st.session_state.last_toggle.astimezone(local_tz).time())
                if st.button("Update Start Time"):
                    # Combine current date with new time
                    current_date = st.session_state.last_toggle.astimezone(
                        local_tz).date()
                    new_start_datetime = datetime.combine(
                        current_date, new_start_time)
                    new_start_utc = local_tz.localize(
                        new_start_datetime).astimezone(pytz.UTC)

                    # Update the last toggle time
                    st.session_state.last_toggle = new_start_utc
                    st.success("Start time updated!")
                    st.rerun()

# Manual entry section
with st.expander("Add Past Activity"):
    col1, col2 = st.columns(2)
    with col1:
        activity = st.selectbox("Activity", ["Standing", "Sitting"])
    with col2:
        entry_date = st.date_input("Date", date.today())

    time_col1, time_col2 = st.columns(2)
    with time_col1:
        start_time = st.time_input("Start Time", latest_time)
    with time_col2:
        end_time = st.time_input("End Time",
                                 (datetime.combine(date.today(), latest_time) +
                                  timedelta(minutes=30)).time())

    if st.button("Add Activity"):
        # Combine date and time
        start_datetime = datetime.combine(entry_date, start_time)
        end_datetime = datetime.combine(entry_date, end_time)

        # Convert to UTC for storage
        start_datetime = local_tz.localize(start_datetime).astimezone(pytz.UTC)
        end_datetime = local_tz.localize(end_datetime).astimezone(pytz.UTC)

        valid, message = validate_time_input(start_datetime, end_datetime)
        if valid:
            duration = (end_datetime - start_datetime).total_seconds() / 60
            new_record = pd.DataFrame({
                'timestamp': [start_datetime],
                'activity': [activity.lower()],
                'duration_minutes': [duration]
            })
            df = pd.concat([df, new_record], ignore_index=True)
            save_activity_data(df)
            st.success("Activity added successfully!")
            st.rerun()
        else:
            st.error(message)

# Daily summary
st.header("Daily Summary")
today = current_time.date()
today_data = df[pd.to_datetime(df['timestamp']).dt.tz_convert(local_tz).dt.date
                == today]

if not today_data.empty:
    total_standing = today_data[today_data['activity'] ==
                                'standing']['duration_minutes'].sum()
    total_sitting = today_data[today_data['activity'] ==
                               'sitting']['duration_minutes'].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Standing Time", f"{total_standing:.1f} minutes")
    with col2:
        st.metric("Total Sitting Time", f"{total_sitting:.1f} minutes")
    with col3:
        health_score, message = calculate_health_score(total_standing)
        st.metric("Health Score", f"{health_score:.1f}%")
        st.caption(message)

    # Visualization with neutral colors
    fig = px.pie(
        values=[total_standing, total_sitting],
        names=['Standing', 'Sitting'],
        title='Daily Activity Distribution',
        color_discrete_sequence=['#4682B4',
                                 '#87CEEB']  # Steel Blue and Sky Blue
    )
    st.plotly_chart(fig)

    # Block-style activity timeline with edit capabilities
    st.subheader("Today's Activities")
    timeline_df = today_data.copy()
    timeline_df = timeline_df.sort_values('timestamp')

    for idx, row in timeline_df.iterrows():
        start_time = row['timestamp'].tz_convert(local_tz)
        end_time = start_time + pd.Timedelta(minutes=row['duration_minutes'])

        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
            with col1:
                activity_emoji = "🧍" if row['activity'] == 'standing' else "🪑"
                st.write(f"{activity_emoji} {row['activity'].title()}")
            with col2:
                st.write(f"Start: {start_time.strftime('%I:%M %p')}")
            with col3:
                st.write(f"End: {end_time.strftime('%I:%M %p')}")
            with col4:
                if st.button("Edit", key=f"edit_{idx}"):
                    st.session_state.editing_activity = idx
                    st.rerun()
            with col5:
                if st.button("🗑️", key=f"delete_{idx}"):
                    df.drop(idx, inplace=True)
                    save_activity_data(df)
                    st.rerun()

            # Edit form
            if st.session_state.editing_activity == idx:
                with st.form(f"edit_form_{idx}"):
                    new_activity = st.selectbox(
                        "Activity", ["Standing", "Sitting"],
                        index=0 if row['activity'] == 'standing' else 1,
                        key=f"activity_{idx}")
                    new_start = st.time_input("Start Time",
                                              start_time.time(),
                                              key=f"start_{idx}")
                    new_end = st.time_input("End Time",
                                            end_time.time(),
                                            key=f"end_{idx}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Save"):
                            # Update the activity
                            new_start_dt = datetime.combine(
                                start_time.date(), new_start)
                            new_end_dt = datetime.combine(
                                start_time.date(), new_end)

                            new_start_dt = local_tz.localize(
                                new_start_dt).astimezone(pytz.UTC)
                            new_end_dt = local_tz.localize(
                                new_end_dt).astimezone(pytz.UTC)

                            if new_end_dt > new_start_dt:
                                duration = (new_end_dt -
                                            new_start_dt).total_seconds() / 60
                                df.at[idx, 'timestamp'] = new_start_dt
                                df.at[idx, 'activity'] = new_activity.lower()
                                df.at[idx, 'duration_minutes'] = duration
                                save_activity_data(df)
                                st.session_state.editing_activity = None
                                st.rerun()
                            else:
                                st.error("End time must be after start time")
                    with col2:
                        if st.form_submit_button("Cancel"):
                            st.session_state.editing_activity = None
                            st.rerun()
else:
    st.info(
        "No activity recorded today. Start tracking by using the toggle button above!"
    )

# Simplified health recommendations (always visible)
st.header("Quick Health Tips")
st.markdown("""
- 🎯 Aim for 2-4 hours of standing during workday
- 🔄 Switch positions every 30-60 minutes
- 👟 Use comfortable footwear when standing
- 👀 Keep screen at eye level
""")
