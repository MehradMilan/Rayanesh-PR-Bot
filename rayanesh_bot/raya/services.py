import re
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import typing
import logging

from django.conf import settings

from user.models import TelegramUser

logger = logging.getLogger(__name__)

_drive_service = None


def get_drive_service():
    if _drive_service is None:
        _drive_service = build(
            "drive", "v3", credentials=settings.GOOGLE_CREDENTIALS_PATH
        )
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
    user_email: typing.List[TelegramUser],
    access_level: str,
    is_directory: bool,
) -> typing.Tuple[bool, str]:

    try:
        permission = {"type": "user", "role": access_level, "emailAddress": user_email}

        get_drive_service().permissions().create(
            fileId=document_id, body=permission
        ).execute()

    except HttpError as error:
        logger.error(
            f"Drive API error for document_id: {document_id} where is_directory:{is_directory}: {error}"
        )
        return False, str(error)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False, str(e)

    return True, None
