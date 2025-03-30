import typing
from datetime import datetime
import os
import subprocess
from pathlib import Path
from asgiref.sync import sync_to_async
import pytz

from django.conf import settings
import celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from core.celery import DB_POSTGRES_BACKUP_QUEUE, GATEKEEPERS_QUEUE, app as celery_app
from django.utils import timezone

import reusable.db_sync_services as db_sync_services
from user.models import TelegramUser, Group, GroupMembership
from document.models import Document, DocumentGroupAccess, DocumentUserAccess
import raya.services
import reusable.telegram_bots
import raya.models
import reusable.persian_response as persian

logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender: celery.Celery, **_) -> None:
    sender.add_periodic_task(
        crontab(minute=0, hour=23),
        backup_postgres_database.s(),
        name="backup_postgres_database",
        queue=DB_POSTGRES_BACKUP_QUEUE,
    )
    sender.add_periodic_task(
        crontab(minute=1, hour="*"),
        check_gate_status.s(),
        name="check_gate_status",
        queue=GATEKEEPERS_QUEUE,
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


async def update_user_access_joined_group(
    group: Group, user: TelegramUser
) -> typing.Tuple[bool, typing.Dict[str, str]]:
    failed_docs: typing.Dict[str, str] = {}

    group_doc_accesses: typing.List[DocumentGroupAccess] = await sync_to_async(
        lambda: list(DocumentGroupAccess.objects.filter(group=group, is_active=True))
    )()

    for group_access in group_doc_accesses:
        document: Document = (
            await db_sync_services.get_document_from_document_group_access(group_access)
        )
        access_level: str = group_access.access_level

        try:
            user_access, created = (
                await db_sync_services.get_or_create_document_user_access(
                    document=document, user=user, access_level=access_level
                )
            )

            if created:
                logger.info(f"Creating new access: {document.google_id} → {user.email}")

                is_ok, error = raya.services.give_document_access_to_user(
                    document_id=document.google_id,
                    user_email=user.email,
                    access_level=access_level,
                )

                if not is_ok:
                    failed_docs[document.google_id] = error
                    continue

            else:
                user_access.access_count += 1
                await sync_to_async(user_access.save)()

        except Exception as e:
            logger.exception(
                f"Unexpected error for {document.google_id} → {user.email}"
            )
            failed_docs[document.google_id] = str(e)

    return (not failed_docs, failed_docs)


async def revoke_access_from_group(
    group: Group, document_id: str
) -> typing.Tuple[bool, typing.Dict[str, str]]:
    """
    Revoke access to a document from all users in the specified group.
    Removes the group access, reduces user access count, and revokes access on Google.
    """
    group_doc_accesses = await sync_to_async(
        lambda: list(
            DocumentGroupAccess.objects.filter(
                group=group, document__google_id=document_id
            )
        )
    )()

    if not group_doc_accesses:
        return False, {
            "document": "Access record not found for this group and document."
        }

    for group_access in group_doc_accesses:
        await sync_to_async(group_access.delete)()

    failed_users = {}
    group_members = await db_sync_services.get_group_members(group)

    for user in group_members:
        try:
            user_access = await sync_to_async(
                lambda: DocumentUserAccess.objects.filter(
                    document__google_id=document_id, user=user
                )
            )()

            if user_access:
                user_access.access_count -= 1

                if user_access.access_count <= 0:
                    is_ok, error = raya.services.revoke_document_access_from_user(
                        document_id=document_id,
                        user_email=user.email,
                    )

                    if not is_ok:
                        failed_users[user.email] = error
                        continue

                    await sync_to_async(user_access.delete)()

                else:
                    await sync_to_async(user_access.save)()

        except Exception as e:
            failed_users[user.email] = str(e)

    return (not failed_users, failed_users)


async def remove_user_from_group(
    user: TelegramUser, group: Group
) -> typing.Tuple[bool, typing.Dict[str, str]]:
    membership: GroupMembership = await sync_to_async(
        lambda: GroupMembership.objects.filter(group=group, user=user).first()
    )()
    await sync_to_async(membership.delete)()

    group_doc_accesses = await sync_to_async(
        lambda: list(
            DocumentGroupAccess.objects.filter(group=group)
            .select_related("document")
            .prefetch_related("document__documentuseraccess_set__user")
        )
    )()
    failed_docs = {}
    for doc_access in group_doc_accesses:
        document = doc_access.document
        for user_access in doc_access.document.documentuseraccess_set.all():
            user_access.access_count -= 1
            if user_access.access_count <= 0:
                is_ok, error = raya.services.revoke_document_access_from_user(
                    document_id=document.google_id,
                    user_email=user.email,
                )
                if not is_ok:
                    failed_docs[document.google_id] = error
                    continue
                await sync_to_async(user_access.delete)()
            else:
                await sync_to_async(user_access.save)()
    return (not failed_docs, failed_docs)


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
        reusable.telegram_bots.send_document_sync(
            bot=raya_bot,
            chat_id=settings.HEALTHCHECK_CHAT_ID,
            file_path=str(backup_path),
            filename=backup_filename,
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


@celery.shared_task(name="check_gate_status", queue=GATEKEEPERS_QUEUE)
def check_gate_status():
    tehran_tz = pytz.timezone("Asia/Tehran")
    now = timezone.now().astimezone(tehran_tz)
    current_time = now.time()
    weekday = now.weekday()

    if now.hour == 1:
        for gate in raya.models.Gate.objects.filter(scannable=True).exclude(
            gate_keepers_group__is_null=True
        ):
            if weekday in [3, 4]:  # Thursday (3), Friday (4)
                gate.is_active = False
            else:
                gate.is_active = True
            gate.save()

    telegram_bot = reusable.telegram_bots.get_telegram_bot()
    for gate in raya.models.Gate.objects.filter(scannable=True, is_active=True):
        if (
            not gate.is_open
            and gate.open_from
            and gate.open_to
            and gate.open_from <= current_time <= gate.open_to
        ):
            reusable.telegram_bots.send_message_sync(
                bot=telegram_bot,
                chat_id=gate.gate_keepers_group.chat_id,
                message=persian.OPEN_GATE_MESSAGES.get(
                    now.hour, persian.OPEN_GATE_MESSAGE_DEF
                ).format(id=gate.id),
            )
            logger.info(
                f"Reminded to open the door in Gatekeepers at {now.hour} O'clock."
            )
        elif (
            gate.is_open
            and gate.close_from
            and gate.close_to
            and gate.close_from <= current_time <= gate.close_to
        ):
            reusable.telegram_bots.send_message_sync(
                bot=telegram_bot,
                chat_id=gate.gate_keepers_group.chat_id,
                message=persian.CLOSE_GATE_MESSAGES.get(
                    now.hour, persian.CLOSE_GATE_MESSAGE_DEF
                ).format(id=gate.id),
            )
            logger.info(
                f"Reminded to close the door in Gatekeepers at {now.hour} O'clock."
            )
