import os
import traceback
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
REPORTS_DIR = Path("reports")

def upload_pdf_to_drive(file_name: str, company_name: str, timestamp_str: str) -> str | None:
    """
    Uploads a generated PDF to a specific Google Drive folder and makes it shareable.
    Fails gracefully if credentials or folder ID are missing or invalid.
    """
    try:
        service_account_file = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

        if not service_account_file or not os.path.exists(service_account_file):
            print("  [WARN] Google Drive skipping: GOOGLE_SERVICE_ACCOUNT_JSON not set or invalid path.")
            return None
        
        if not folder_id:
            print("  [WARN] Google Drive skipping: GOOGLE_DRIVE_FOLDER_ID not set.")
            return None

        # Authenticate
        creds = service_account.Credentials.from_service_account_file(
            service_account_file, scopes=SCOPES
        )
        service = build('drive', 'v3', credentials=creds)

        pdf_path = REPORTS_DIR / file_name
        if not pdf_path.exists():
            print(f"  [WARN] Google Drive error: PDF not found at {pdf_path}")
            return None

        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in company_name)
        drive_file_name = f"{safe_name}_{timestamp_str}.pdf"

        # Upload file
        file_metadata = {
            'name': drive_file_name,
            'parents': [folder_id]
        }
        media = MediaFileUpload(str(pdf_path), mimetype='application/pdf', resumable=True)
        
        print(f"  [INFO] Uploading {drive_file_name} to Google Drive...")
        file = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink'
        ).execute()
        
        file_id = file.get('id')
        web_view_link = file.get('webViewLink')

        if not file_id:
            print("  [WARN] Google Drive upload failed: No file ID returned.")
            return None

        # Change permission to 'anyone with link can view'
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }
        service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id'
        ).execute()

        print(f"  [SUCCESS] Uploaded to Google Drive successfully. Link: {web_view_link}")
        return web_view_link

    except Exception as e:
        print(f"  [ERROR] Google Drive upload error: {e}")
        # traceback.print_exc() # Optional: print traceback for debugging without breaking workflow
        return None
