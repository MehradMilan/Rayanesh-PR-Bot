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


def extract_google_id(link: str) -> str | None:
    match = re.search(r"/d/([a-zA-Z0-9-_]+)", link)
    return match.group(1) if match else None


def give_document_access_to_user(
    document_id: str, user_email: typing.List[TelegramUser], access_level: str
) -> typing.Tuple[bool, str]:

    try:
        permission = {"type": "user", "role": access_level, "emailAddress": user_email}

        get_drive_service().permissions().create(
            fileId=document_id, body=permission
        ).execute()

    except HttpError as error:
        logger.error(error)
        return False, error.error_details
    except Exception as e:
        logger.error(e)
        return False, e

    return True, None
