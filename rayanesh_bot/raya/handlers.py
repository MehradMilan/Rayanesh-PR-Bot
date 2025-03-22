import logging
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import typing

from django.utils import timezone

from user.models import TelegramUser, GroupMembership
import reusable.db_sync_services as db_sync_services
import reusable.persian_response as persian
import reusable.telegram_bot.bot_command

logger = logging.getLogger(__name__)


async def accept_join(update: Update, context: CallbackContext) -> None:
    user: User = update.effective_user

    telegram_user: TelegramUser = await db_sync_services.get_telegram_user_by_id(
        user.id
    )
    if telegram_user is None or not telegram_user.is_authorized:
        await update.message.reply_text(persian.USER_UNAUTHORIZED)
        return
    if telegram_user.user_type != TelegramUser.MANAGER_USER:
        await update.message.reply_text(persian.USER_HAS_NO_ACCESS)
        return

    pending_reqs: typing.List[GroupMembership] = (
        await db_sync_services.get_pending_group_memberships()
    )
    if not pending_reqs:
        await update.message.reply_text(persian.NO_PENDING_JOIN_REQUESTS)
        return

    for membership in pending_reqs:
        user = membership.user
        group = membership.group

        keyboard = [
            [
                InlineKeyboardButton(
                    f"تایید {user.username or user.name}",
                    callback_data=f"approve:{membership.id}",
                ),
                InlineKeyboardButton(
                    f"رد {user.username or user.name}",
                    callback_data=f"deny:{membership.id}",
                ),
            ]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Join request for {user.username or user.name} to group '{group.title}'",
            reply_markup=reply_markup,
        )


async def approve_join_request(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    action, membership_id = query.data.split(":")
    membership: GroupMembership = db_sync_services.get_group_membership_by_id(
        membership_id=membership_id
    )

    if action == "approve":
        membership.is_approved = True
        membership.joined_at = timezone.now()
        db_sync_services.save_group_membership(membership)

        telegram_link: str = membership.group.telegram_chat_link
        if telegram_link:
            bot = reusable.telegram_bot.bot_command.get_telegram_bot()
            bot.send_message(
                chat_id=membership.user.telegram_id,
                text=f"به گروه خوش اومدی ستون.\n{telegram_link}",
            )

        await query.message.reply_text(
            f"✅ {membership.user.username or membership.user.name} has been approved."
        )

    elif action == "deny":
        await query.message.reply_text(
            f"❌ User {membership.user.username or membership.user.name}'s request has been denied."
        )
