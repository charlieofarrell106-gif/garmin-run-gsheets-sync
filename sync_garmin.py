import os
import json
import datetime
from garminconnect import Garmin
from google.oauth2.service_account import Credentials
import gspread

def main():
    print("Starting Garmin Wellness & Activity sync...")
    
    # 1. Get credentials
    garmin_email = os.environ.get('GARMIN_EMAIL')
    garmin_password = os.environ.get('GARMIN_PASSWORD')
    google_creds_json = os.environ.get('GOOGLE_CREDENTIALS')
    sheet_id = os.environ.get('SHEET_ID')
    
    if not all([garmin_email, garmin_password, google_creds_json, sheet_id]):
        print("❌ Missing required environment variables")
        return

    # 2. Connect to Garmin
    try:
        garmin = Garmin(garmin_email, garmin_password)
        garmin.login()
        print("✅ Connected to Garmin")
    except Exception as e:
        print(f"❌ Failed to connect to Garmin: {e}")
        return

    # 3. Connect to Google Sheets
    try:
        creds_dict = json.loads(google_creds_json)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        gc = gspread.authorize(creds)
        # Opens the specific tab named "Garmin Data"
        sheet = gc.open_by_key(sheet_id).worksheet("Garmin Data")
        print("✅ Connected to Google Sheets")
    except Exception as e:
        print(f"❌ Failed to connect to Google Sheets: {e}")
        return

    # 4. Fetch Wellness Data for today
    today = datetime.date.today().isoformat()
    print(f"Fetching wellness stats for {today}...")
    try:
        stats = garmin.get_stats(today)
        sleep_data = garmin.get_sleep_data(today)
        hrv_data = garmin.get_hrv_data(today)
        
        sleep_score = sleep_data.get('dailySleepDTO', {}).get('sleepScore', 0)
        hrv_val = hrv_data.get('hrvSummary', {}).get('lastNightAvg', 0)
        rhr_val = stats.get('restingHeartRate', 0)
    except:
        sleep_score, hrv_val, rhr_val = 0, 0, 0

    # 5. Fetch and Process last 10 Activities
    activities = garmin.get_activities(0, 10)
    existing_dates = set(sheet.col_values(1)) # Check column A for existing dates
    
    new_entries = 0
    for activity in activities:
        activity_date = activity.get('startTimeLocal', '')[:10]
        
        if activity_date in existing_dates:
            continue
            
        activity_name = activity.get('activityName', 'Activity')
        distance_km = round(activity.get('distance', 0) / 1000, 2)
        duration_min = round(activity.get('duration', 0) / 60, 1)
        avg_hr = activity.get('averageHR', 0) or 0
        calories = activity.get('calories', 0) or 0
        activity_type = activity.get('activityType', {}).get('typeKey', 'other')

        # Row matches: Date, Name, Distance, Duration, HR, Calories, Type, Sleep, HRV, RHR
        new_row = [
            activity_date, activity_name, distance_km, duration_min, 
            avg_hr, calories, activity_type, sleep_score, hrv_val, rhr_val
        ]
        
        sheet.append_row(new_row)
        print(f"✅ Logged: {activity_date} - {activity_name}")
        new_entries += 1

    print(f"\nDone! Added {new_entries} new entries.")

if __name__ == "__main__":
    main()
