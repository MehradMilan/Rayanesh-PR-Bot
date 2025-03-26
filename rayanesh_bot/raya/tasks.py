import typing
from datetime import datetime
import os
import subprocess
from pathlib import Path
import asyncio

from django.conf import settings
import celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from core.celery import DB_POSTGRES_BACKUP_QUEUE, app as celery_app

import reusable.db_sync_services as db_sync_services
from user.models import TelegramUser, Group
from document.models import Document
import raya.services
import reusable.telegram_bots

logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender: celery.Celery, **_) -> None:
    sender.add_periodic_task(
        crontab(minute="*/2"),
        backup_postgres_database.s(),
        name="backup_postgres_database",
        queue=DB_POSTGRES_BACKUP_QUEUE,
    )


async def share_document_with_group(
    document: Document, group: Group, access_level: str
) -> typing.Tuple[bool, typing.Dict[str, str]]:
    """
    Shares the document with each user of the group and creates the corresponding DocumentUserAccess.
    """
    document_group_access, new_access = (
        await db_sync_services.get_or_create_document_group_access(
            document=document, group=group, access_level=access_level
        )
    )
    group_members: typing.List[TelegramUser] = await db_sync_services.get_group_members(
        group
    )
    failed_users: typing.Dict[str, str] = {}

    for telegram_user in group_members:
        is_ok, error_response = raya.services.give_document_access_to_user(
            document_id=document.google_id,
            user_email=telegram_user.email,
            access_level=access_level,
        )
        if not is_ok:
            failed_users[telegram_user.email] = error_response
            continue

        access, created = await db_sync_services.get_or_create_document_user_access(
            user=telegram_user, document=document, access_level=access_level
        )
        if not created and new_access:
            access.access_count += 1
            access.save()

    return (not failed_users, failed_users)


@celery.shared_task(name="backup_postgres_database", queue=DB_POSTGRES_BACKUP_QUEUE)
def backup_postgres_database():
    """
    Performs a PostgreSQL database backup and sends it to a Telegram bot.
    Uses safe subprocess practices and handles errors cleanly.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"db_backup_{timestamp}.sql"
    backup_dir = Path(settings.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path = backup_dir / backup_filename

    logger.info(f"Starting database backup to: {backup_path}")

    try:
        with open(backup_path, "wb") as f:
            result = subprocess.run(
                [
                    "pg_dump",
                    "-U",
                    settings.POSTGRES_USER,
                    "-h",
                    settings.POSTGRES_HOST,
                    settings.POSTGRES_DB,
                ],
                stdout=f,
                stderr=subprocess.PIPE,
                check=True,
                env={**os.environ, "PGPASSWORD": settings.POSTGRES_PASSWORD},
            )

        logger.info(f"Database backup successful: {backup_path}")

        raya_bot = reusable.telegram_bots.get_raya_bot()
        with open(backup_path, "rb") as backup_file:
            asyncio.run(
                raya_bot.send_document(
                    chat_id=settings.HEALTHCHECK_CHAT_ID,
                    document=backup_file,
                    filename=backup_filename,
                )
            )

        logger.info(f"Backup sent to Telegram: {settings.HEALTHCHECK_CHAT_ID}")

    except subprocess.CalledProcessError as e:
        logger.error(f"pg_dump failed: {e.stderr.decode().strip()}")
    except Exception as e:
        logger.exception(f"Unexpected error during backup: {e}")
    finally:
        if backup_path.exists():
            backup_path.unlink()
            logger.info(f"Temporary backup file deleted: {backup_path}")
