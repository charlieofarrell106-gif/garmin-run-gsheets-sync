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

    # 2. Connect to Google Sheets
    print("Connecting to Google Sheets...")
    try:
        creds_dict = json.loads(google_creds_json)
        creds = Credentials.from_service_account_info(
            creds_dict,
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        gc = gspread.authorize(creds)
        
        # Open the spreadsheet
        doc = gc.open_by_key(sheet_id)
        
        # USE THE FIRST TAB NO MATTER WHAT IT IS NAMED
        sheet = doc.get_worksheet(0) 
        print(f"✅ Connected to Sheet: {doc.title}, Tab: {sheet.title}")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    # Fetch and Process last 10 Activities
    activities = garmin.get_activities(0, 10)
    
    # Get all dates currently in Column A to avoid duplicates
    existing_dates = sheet.col_values(1)
    
    new_entries = 0
    for activity in activities:
        activity_date = activity.get('startTimeLocal', '')[:10]
        if activity_date in existing_dates:
            continue
            
        new_row = [
            activity_date, 
            activity.get('activityName', 'Activity'),
            round(activity.get('distance', 0) / 1000, 2),
            round(activity.get('duration', 0) / 60, 1),
            activity.get('averageHR', 0),
            activity.get('calories', 0),
            activity.get('activityType', {}).get('typeKey', 'other')
        ]
        
        sheet.append_row(new_row)
        print(f"✅ Added: {activity_date}")
        new_entries += 1
    print(f"\nDone! Added {new_entries} new entries.")

if __name__ == "__main__":
    main()
