import logging
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
import typing

from django.utils import timezone

import reusable.db_sync_services
from user.models import TelegramUser, GroupMembership, Group
from document.models import Document
import reusable.db_sync_services as db_sync_services
import reusable.persian_response as persian
import reusable.telegram_bots
import raya.states
import raya.services
import raya.tasks

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
            f"Join request for {user.name} with username {user.username} to group '{group.title}'",
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
            await bot.send_message(
                chat_id=user.telegram_id,
                text=persian.WELCOME_TO_GROUP.format(telegram_link),
            )

        await query.message.reply_text(f"✅ {user.username or user.name} تایید شد.")

    elif action == "deny":
        await query.message.reply_text(f"❌ {user.username or user.name} رد شد.")


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
        f"📎 لینک عضویت در گروه:\n{group.join_group_uri}"
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


async def give_access(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if not telegram_user.is_authorized:
        await update.message.reply_text(persian.USER_UNAUTHORIZED)
        return ConversationHandler.END

    if telegram_user.user_type != TelegramUser.MANAGER_USER:
        await update.message.reply_text(persian.USER_HAS_NO_ACCESS)
        return ConversationHandler.END

    context.user_data["owner_user"] = telegram_user

    groups = await db_sync_services.get_all_active_groups()

    if not groups:
        await update.message.reply_text(persian.NO_ACTIVE_GROUP)
        return ConversationHandler.END

    message = "Please select a group to give access:\n"
    for group in groups:
        message += f"/group_{group.id} - {group.title}\n"

    await update.message.reply_text(message)

    return raya.states.SELECT_GROUP


async def select_group(update: Update, context: CallbackContext) -> int:
    message_text = update.message.text.strip()

    group_id = int(message_text.split("_")[1])
    group = await db_sync_services.get_group_by_id(group_id)

    if not group:
        await update.message.reply_text(persian.GROUP_NOT_FOUND)
        return ConversationHandler.END

    context.user_data["selected_group"] = group

    await update.message.reply_text("Please send the document link to share:")

    return raya.states.ENTER_DOC_LINK


async def enter_doc_link(update: Update, context: CallbackContext) -> int:
    link = update.message.text.strip()
    user: TelegramUser = context.user_data["owner_user"]

    google_id, is_directory = raya.services.extract_google_id_and_type(link)
    if google_id is None:
        await update.message.reply_text("Invalid document link. Please try again.")
        return raya.states.ENTER_DOC_LINK

    document, created = await db_sync_services.get_or_create_document(
        google_id, link, user, is_directory=is_directory
    )

    context.user_data["document"] = document

    if created:
        await update.message.reply_text(
            "Document doesn't exist in the system. Please provide the directory link:"
        )
        return raya.states.CONFIRM_DOC
    return await send_access_keyboard(update)


async def send_access_keyboard(update: Update) -> int:
    keyboard = [
        [InlineKeyboardButton("View Access", callback_data="view")],
        [InlineKeyboardButton("Comment Access", callback_data="comment")],
        [InlineKeyboardButton("Edit Access", callback_data="edit")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Select the access level for the group:", reply_markup=reply_markup
    )

    return raya.states.ACCESS_LEVEL


async def confirm_doc(update: Update, context: CallbackContext) -> int:
    directory_link = update.message.text.strip()
    directory_id, is_directory = raya.services.extract_google_id_and_type(
        directory_link
    )
    if directory_id is None or not is_directory:
        await update.message.reply_text("Invalid document link. Please try again.")
        return raya.states.CONFIRM_DOC

    document: Document = context.user_data.get("document")
    if not document:
        await update.message.reply_text("No document selected. Please try again.")
        return ConversationHandler.END

    document.directory_id = directory_id
    document.is_finalized = True
    await db_sync_services.save_document(document)

    return await send_access_keyboard(update)


async def set_access_level(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()

    access_level = query.data

    group = context.user_data.get("selected_group")
    document = context.user_data.get("document")

    if not group or not document:
        await query.message.reply_text("Something went wrong, please try again.")
        return

    is_ok, failed_users = await raya.tasks.share_document_with_group(
        document, group, access_level
    )
    if is_ok:
        await query.message.reply_text(
            f"Document has been shared with {group.title} at {access_level} level."
        )
    else:
        member_count = await reusable.db_sync_services.get_group_members_count(group)
        message = f"Failed to give access to {len(failed_users)} out of {member_count} users:\n"
        for user_email, error in failed_users.items():
            message += f"• {user_email}: {error}\n"
    await query.message.reply_text(message)

    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text(persian.CANCEL_CONVERSATION)
    return ConversationHandler.END
