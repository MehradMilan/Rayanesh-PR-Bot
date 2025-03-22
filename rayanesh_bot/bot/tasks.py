import logging
import typing

import reusable.db_sync_services as db_sync_services
import reusable.persian_response as persian
from user.models import TelegramUser

logger = logging.getLogger(__name__)


async def extract_deeplink_from_message(
    message_text: str,
) -> typing.Tuple[str, typing.List[str]]:
    input = message_text.split(" ")
    input.pop(0)
    if input:
        params = input.pop(0).split("-")
        return (params[0], params[1:])
    return (None, [])


async def join_group_request(telegram_user_id, group_id):
    group = await db_sync_services.get_group_by_id(group_id)
    if group is None:
        return persian.GROUP_NOT_FOUND
    user: TelegramUser = await db_sync_services.get_telegram_user_by_id(
        telegram_user_id
    )
    if user is None or not user.is_authorized:
        return persian.USER_UNAUTHORIZED
    else:
        group_membership, created = (
            await db_sync_services.get_or_create_group_membership(
                user=user, group=group
            )
        )
        if created:
            return persian.GROUP_REQUEST_SUCCESS
        else:
            return persian.GROUP_REQUEST_ALREADY_EXIST
