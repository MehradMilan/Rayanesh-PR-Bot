import logging
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import typing

from django.utils import timezone

from user.models import TelegramUser, GroupMembership, Group
import reusable.db_sync_services as db_sync_services
import reusable.persian_response as persian
import reusable.telegram_bots

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
        user: TelegramUser = await db_sync_services.get_user_in_group_membership(
            membership
        )
        group: Group = await db_sync_services.get_group_in_group_membership(membership)

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
    membership: GroupMembership = await db_sync_services.get_group_membership_by_id(
        membership_id=membership_id
    )

    if action == "approve":
        membership.is_approved = True
        membership.joined_at = timezone.now()
        await db_sync_services.save_group_membership(membership)

        group: Group = await db_sync_services.get_group_in_group_membership(membership)
        user: TelegramUser = await db_sync_services.get_user_in_group_membership(
            membership
        )
        telegram_link: str = group.telegram_chat_link
        if telegram_link:
            bot = reusable.telegram_bots.get_telegram_bot()
            bot.send_message(
                chat_id=user.telegram_id,
                text=f"به گروه خوش اومدی ستون.\n{telegram_link}",
            )

        await query.message.reply_text(
            f"✅ {user.username or user.name} has been approved."
        )

    elif action == "deny":
        await query.message.reply_text(
            f"❌ User {user.username or user.name}'s request has been denied."
        )


async def show_group_info(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    _, group_id = query.data.split(":")
    group = await db_sync_services.get_group_by_id(group_id)
    members = await db_sync_services.get_group_members(group)

    member_names = (
        "\n".join([f"- {m.name or m.username}" for m in members]) or "بدون عضو"
    )

    message = (
        f"<b>{group.title}</b>\n"
        f"📅 ساخته‌شده در: {group.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"👥 اعضا: {len(members)}\n"
        f"{member_names}\n\n"
        f"📎 لینک گروه تلگرام:\n{group.join_group_uri}"
    )

    await query.message.reply_text(message, parse_mode="HTML")


async def list_groups(update: Update, context: CallbackContext) -> None:
    user: User = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if telegram_user is None or not telegram_user.is_authorized:
        await update.message.reply_text(persian.USER_UNAUTHORIZED)
        return

    if telegram_user.user_type != TelegramUser.MANAGER_USER:
        await update.message.reply_text(persian.USER_HAS_NO_ACCESS)
        return

    groups = await db_sync_services.get_all_active_groups()
    if not groups:
        await update.message.reply_text(persian.NO_ACTIVE_GROUP)
        return

    keyboard = [
        [InlineKeyboardButton(group.title, callback_data=f"groupinfo:{group.id}")]
        for group in groups
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("لیست گروه‌های فعال:\n", reply_markup=reply_markup)

