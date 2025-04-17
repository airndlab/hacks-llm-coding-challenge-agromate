import logging
import os
import re

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from agroapp.config import settings

logger = logging.getLogger(__name__)


def get_folder_id_from_url(folder_url: str) -> str:
    pattern = r"^https:\/\/drive\.google\.com\/drive\/folders\/([^?\/]+)"
    match = re.search(pattern, folder_url)
    if match:
        return match.group(1)
    raise ValueError(f"Invalid Google Drive Folder url: {folder_url}")


def create_service_account():
    creds = service_account.Credentials.from_service_account_file(
        settings.google_credentials_path,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=creds)


folder_id = get_folder_id_from_url(settings.google_drive_folder_url)
sa = create_service_account()


def upload_report_to_folder(file_path: str) -> str:
    try:
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id]
        }
        media = MediaFileUpload(
            file_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        file = sa.files().create(
            body=file_metadata,
            media_body=media,
            fields='webViewLink'
        ).execute()
        file_url = file.get('webViewLink')
        logger.info(f"Uploaded report '{file_path}' to Google Drive: {file_url}")
        return file_url
    except Exception as e:
        logger.error(f"Error of uploading report '{file_path}': {str(e)}")
        raise Exception(f"Error of uploading report '{file_path}': {str(e)}")
