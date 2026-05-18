import os
import traceback
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def log_lead_to_sheets(lead: dict, report_status: str, drive_link: str | None = None) -> None:
    """
    Appends a new row to the specified Google Sheet with the lead's information.
    Fails gracefully if credentials or sheet ID are missing or invalid.
    """
    try:
        service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        sheet_id = os.getenv("GOOGLE_SHEET_ID")

        if not service_account_file or not os.path.exists(service_account_file):
            print("  [WARN] Google Sheets skipping: GOOGLE_SERVICE_ACCOUNT_JSON not set or invalid path.")
            return
        
        if not sheet_id:
            print("  [WARN] Google Sheets skipping: GOOGLE_SHEET_ID not set.")
            return

        # Authenticate
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES
        )
        service = build('sheets', 'v4', credentials=creds)

        # Prepare row data: Timestamp, Name, Email, Company, Website URL, Report Status, PDF Drive Link
        timestamp_str = datetime.utcnow().isoformat() + "Z"
        row_data = [
            timestamp_str,
            lead.get('name', ''),
            lead.get('email', ''),
            lead.get('companyName', ''),
            lead.get('website', ''),
            report_status,
            drive_link or "Not uploaded"
        ]

        # The range 'Sheet1' is a common default. If we don't know the exact sheet name,
        # providing the spreadsheet ID and a generic range often works to append to the first sheet.
        # Alternatively, using A:G as range.
        range_name = 'A:G' 

        body = {
            'values': [row_data]
        }

        print(f"  [INFO] Logging lead {lead.get('email')} to Google Sheets...")
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body=body
        ).execute()

        updates = result.get('updates', {})
        updated_cells = updates.get('updatedCells', 0)
        print(f"  [SUCCESS] Logged to Google Sheets successfully ({updated_cells} cells updated).")

    except Exception as e:
        print(f"  [ERROR] Google Sheets logging error: {e}")
        # traceback.print_exc() # Optional for debugging
