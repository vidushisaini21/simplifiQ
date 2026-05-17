import os
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv

load_dotenv()

# Path to the Google Service Account JSON file
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")

# Define Sheet and Drive Config
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

def get_google_service(api_name: str, api_version: str):
    """Initializes and returns a Google API service."""
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"  ⚠️  Google Credentials file not found at {CREDENTIALS_FILE}.")
        return None
        
    try:
        creds = service_account.Credentials.from_service_account_file(
            CREDENTIALS_FILE, scopes=SCOPES)
        service = build(api_name, api_version, credentials=creds)
        return service
    except Exception as e:
        print(f"  ❌ Failed to build Google {api_name} service: {e}")
        return None

def append_to_sheet(lead: dict, status: str):
    """
    Appends lead data to a Google Sheet.
    Includes: Name, Email, Company, Timestamp, Report Status
    """
    if not SPREADSHEET_ID:
        print("  ⚠️  GOOGLE_SHEET_ID not set. Skipping Sheets integration.")
        return

    service = get_google_service('sheets', 'v4')
    if not service:
        return

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values = [[lead.get("name"), lead.get("email"), lead.get("companyName"), timestamp, status]]
        
        body = {'values': values}
        range_name = 'Sheet1!A:E'  # Assumes standard first sheet Name
        
        result = service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()

        print(f"  ✅ Added lead to Google Sheets. Updated cells: {result.get('updates').get('updatedCells')}")
    except Exception as e:
        print(f"  ❌ Error appending to Google Sheets: {e}")

def upload_to_drive(file_name: str, file_path: str):
    """
    Uploads a generated PDF to a specific Google Drive folder.
    """
    if not DRIVE_FOLDER_ID:
        print("  ⚠️  GOOGLE_DRIVE_FOLDER_ID not set. Skipping Drive archiving.")
        return

    service = get_google_service('drive', 'v3')
    if not service:
        return

    try:
        file_metadata = {
            'name': file_name,
            'parents': [DRIVE_FOLDER_ID]
        }
        
        media = MediaFileUpload(file_path, mimetype='application/pdf', resumable=True)
        
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"  ✅ Uploaded PDF '{file_name}' to Google Drive with ID: {uploaded_file.get('id')}")
    except Exception as e:
        print(f"  ❌ Error uploading to Google Drive: {e}")
