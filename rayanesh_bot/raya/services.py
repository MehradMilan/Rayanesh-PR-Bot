import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
import typing
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_drive_service = None


def get_drive_service():
    global _drive_service
    if _drive_service is None:
        creds = Credentials.from_service_account_file(
            settings.GOOGLE_CREDENTIALS_PATH,
            scopes=[
                "https://www.googleapis.com/auth/drive",
                "https://www.googleapis.com/auth/documents",
            ],
        )
        _drive_service = build("drive", "v3", credentials=creds)
    return _drive_service


def extract_google_id_and_type(link: str) -> typing.Tuple[str | None, bool | None]:
    """
    Extracts the Google ID and determines whether it's a file or folder.
    Returns a tuple: (google_id, is_directory)
    """
    # Match document-style links
    doc_match = re.search(r"/d/([a-zA-Z0-9-_]+)", link)
    if doc_match:
        return doc_match.group(1), False

    # Match folder-style links
    folder_match = re.search(r"/folders/([a-zA-Z0-9-_]+)", link)
    if folder_match:
        return folder_match.group(1), True

    return None, None


def give_document_access_to_user(
    document_id: str,
    user_email: str,
    access_level: str,
) -> typing.Tuple[bool, str]:

    try:
        permission = {"type": "user", "role": access_level, "emailAddress": user_email}

        get_drive_service().permissions().create(
            fileId=document_id, body=permission
        ).execute()

    except HttpError as error:
        logger.error(f"Drive API error for document_id: {document_id}: {error}")
        return False, str(error)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False, str(e)

    return True, None


def revoke_document_access_from_user(
    document_id: str, user_email: str
) -> typing.Tuple[bool, str | None]:
    try:
        permissions = (
            get_drive_service().permissions().list(fileId=document_id).execute()
        )
        for permission in permissions.get("permissions", []):
            if permission.get("emailAddress") == user_email:
                get_drive_service().permissions().delete(
                    fileId=document_id, permissionId=permission["id"]
                ).execute()
                return True, None
        return False, "No permission found for user."
    except HttpError as e:
        logger.error(e)
        return False, str(e)
    except Exception as e:
        logger.error(e)
        return False, str(e)
