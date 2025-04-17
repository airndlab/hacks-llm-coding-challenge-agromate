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


def upload_word_file_to_folder(file_path: str) -> tuple[str, str]:
    try:
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id]
        }
        media = MediaFileUpload(
            file_path,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        file = sa.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        file_id = file.get('id')
        file_url = file.get('webViewLink')
        logger.info(f"Uploaded word file '{file_path}' to Google Drive: {file_url}")
        return file_id, file_url
    except Exception as e:
        logger.error(f"Error uploading word file '{file_path}': {e}")
        raise Exception(f"Error uploading word file '{file_path}': {e}")


def upload_excel_file_to_folder(file_path: str) -> tuple[str, str]:
    try:
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id],
            'mimeType': 'application/vnd.google-apps.spreadsheet',
            'properties': {
                'locale': 'ru_RU'
            }
        }
        media = MediaFileUpload(
            file_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        file = sa.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        file_id = file.get('id')
        file_url = file.get('webViewLink')
        logger.info(f"Uploaded excel '{file_path}' to Google Drive: {file_url}")
        return file_id, file_url
    except Exception as e:
        logger.error(f"Error of uploading excel '{file_path}': {str(e)}")
        raise Exception(f"Error of uploading excel '{file_path}': {str(e)}")


def overwrite_excel_file_by_id(file_id: str, file_path: str):
    try:
        media = MediaFileUpload(
            file_path,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        file = sa.files().update(
            fileId=file_id,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        file_id = file.get('id')
        file_url = file.get('webViewLink')
        logger.info(f"Overwrote excel '{file_path}' in Google Drive: {file_url}")
        return file_id, file_url
    except Exception as e:
        logger.error(f"Error of overwriting excel '{file_path}': {str(e)}")
        raise Exception(f"Error of overwriting excel '{file_path}': {str(e)}")
