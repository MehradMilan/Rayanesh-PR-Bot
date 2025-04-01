import logging
from telegram import Update, User, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
import typing
import re
from asgiref.sync import sync_to_async
from dateutil.parser import parse

from django.utils import timezone
from django.conf import settings

import reusable.db_sync_services
from user.models import TelegramUser, GroupMembership, Group
from document.models import (
    Document,
    VIEW_ACCESS_LEVEL,
    COMMENT_ACCESS_LEVEL,
    EDIT_ACCESS_LEVEL,
)
import reusable.db_sync_services as db_sync_services
import reusable.persian_response as persian
import reusable.telegram_bots
import raya.states
import raya.services
import raya.tasks
from raya.models import Notification

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
    user: TelegramUser = await db_sync_services.get_user_in_group_membership(membership)

    if action == "approve":
        membership.is_approved = True
        membership.joined_at = timezone.now()
        await db_sync_services.save_group_membership(membership)

        group: Group = await db_sync_services.get_group_in_group_membership(membership)

        telegram_link: str = group.telegram_chat_link
        if telegram_link:
            bot = reusable.telegram_bots.get_telegram_bot()
            await bot.send_message(
                chat_id=user.telegram_id,
                text=persian.WELCOME_TO_GROUP.format(telegram_link),
            )
        result, errors = await raya.tasks.update_user_access_joined_group(group, user)
        if result:
            await query.message.reply_text(
                "User access updated for all group documents."
            )
        else:
            await query.message.reply_text(
                "Some document access updates failed:\n"
                + "\n".join(f"{doc_id}: {error}" for doc_id, error in errors.items())
            )

        await query.message.reply_text(f"✅ {user.username or user.name} تایید شد.")

    elif action == "deny":
        await sync_to_async(membership.delete)()
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
    match = re.match(r"^/(\w+)_([\d]+)(?:@[\w\d_]+)?$", message_text)
    group_id = int(match.group(2))
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
        [InlineKeyboardButton("View Access", callback_data=VIEW_ACCESS_LEVEL)],
        [InlineKeyboardButton("Comment Access", callback_data=COMMENT_ACCESS_LEVEL)],
        [InlineKeyboardButton("Edit Access", callback_data=EDIT_ACCESS_LEVEL)],
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


async def revoke_access_start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if (
        not telegram_user.is_authorized
        or telegram_user.user_type != TelegramUser.MANAGER_USER
    ):
        await update.message.reply_text(
            "You are not authorized to perform this action."
        )
        return ConversationHandler.END

    groups = await db_sync_services.get_all_active_groups()
    if not groups:
        await update.message.reply_text("There are no active groups.")
        return ConversationHandler.END

    message = "Select the group to revoke access from:\n"
    for group in groups:
        message += f"/group_{group.id} - {group.title}\n"

    await update.message.reply_text(message)
    return raya.states.SELECT_GROUP


async def revoke_select_group(update: Update, context: CallbackContext) -> int:
    text = update.message.text.strip()
    match = re.match(r"^/(\w+)_([\d]+)(?:@[\w\d_]+)?$", text)
    group_id = int(match.group(2))
    group = await db_sync_services.get_group_by_id(group_id)

    if not group:
        await update.message.reply_text("Group not found.")
        return ConversationHandler.END

    context.user_data["selected_group"] = group
    await update.message.reply_text(
        "Please send the document link to revoke access from:"
    )
    return raya.states.ENTER_DOC_LINK


async def revoke_process_link(update: Update, context: CallbackContext) -> int:
    link = update.message.text.strip()
    group = context.user_data.get("selected_group")
    google_id, link_type = raya.services.extract_google_id_and_type(link)

    if not google_id:
        await update.message.reply_text("Invalid link. Try again.")
        return ConversationHandler.END

    result, failed_users = await raya.tasks.revoke_access_from_group(group, google_id)

    if result:
        await update.message.reply_text(
            "Access successfully revoked from group and all users."
        )
    else:
        message = (
            f"Access revoked from group, but some user revocations failed:\n"
            + "\n".join(f"• {email}: {error}" for email, error in failed_users.items())
        )
        await update.message.reply_text(message)

    return ConversationHandler.END


async def remove_user_start(update: Update, context: CallbackContext) -> int:
    user = update.effective_user
    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if (
        not telegram_user.is_authorized
        or telegram_user.user_type != TelegramUser.MANAGER_USER
    ):
        await update.message.reply_text(
            "You are not authorized to perform this action."
        )
        return ConversationHandler.END

    groups = await db_sync_services.get_all_active_groups()
    if not groups:
        await update.message.reply_text("There are no active groups.")
        return ConversationHandler.END

    message = "Select the group to remove a user from:\n"
    for group in groups:
        message += f"/group_{group.id} - {group.title}\n"

    await update.message.reply_text(message)
    return raya.states.SELECT_GROUP


async def remove_select_group(update: Update, context: CallbackContext) -> int:
    text = update.message.text.strip()
    match = re.match(r"^/(\w+)_([\d]+)(?:@[\w\d_]+)?$", text)
    group_id = int(match.group(2))
    group = await db_sync_services.get_group_by_id(group_id)

    if not group:
        await update.message.reply_text("Group not found.")
        return ConversationHandler.END

    context.user_data["selected_group"] = group

    group_members = await db_sync_services.get_group_members(group)
    if not group_members:
        await update.message.reply_text("No members in this group.")
        return ConversationHandler.END

    message = "Select the user to remove:\n"
    for member in group_members:
        message += f"/remove_user_{member.telegram_id} - {member.name}\n"

    await update.message.reply_text(message)
    return raya.states.SELECT_USER


async def remove_user(update: Update, context: CallbackContext) -> int:
    text = update.message.text.strip()
    match = re.match(r"^/(\w+)_([\d]+)(?:@[\w\d_]+)?$", text)
    user_id = int(match.group(2))
    group = context.user_data.get("selected_group")

    if not group:
        await update.message.reply_text("No group selected.")
        return ConversationHandler.END

    user_to_remove = await db_sync_services.get_telegram_user_by_id(user_id)
    if not user_to_remove:
        await update.message.reply_text("User not found.")
        return ConversationHandler.END

    try:
        result, failed_docs = await raya.tasks.remove_user_from_group(
            user=user_to_remove, group=group
        )
        if result:
            await update.message.reply_text(
                f"User {user_to_remove.name} has been removed from {group.title}."
            )
        else:
            message = (
                f"User access revoked from documents in the group, but some document revocations failed:\n"
                + "\n".join(
                    f"• document-{doc_id}: {error}"
                    for doc_id, error in failed_docs.items()
                )
            )
            await update.message.reply_text(message)
    except Exception as e:
        await update.message.reply_text(str(e))

    return ConversationHandler.END


async def send_notification_start(update: Update, context: CallbackContext):
    check = await check_private_and_manager(update, context)
    if check is not None:
        return check
    groups = await sync_to_async(lambda: Group.objects.filter(is_active=True))()

    keyboard = [
        [InlineKeyboardButton(group.name, callback_data=f"send_to_group_{group.id}")]
        for group in groups
    ]

    keyboard.append(
        [InlineKeyboardButton("🌬 All users", callback_data="send_to_all_users")]
    )

    await update.message.reply_text(
        "Select the group to send the notification.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return raya.states.SELECT_GROUP


async def select_group(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()

    selected_target = query.data

    if selected_target != "send_to_all_users":
        group_id = int(selected_target.split("_")[2])
        group = await sync_to_async(lambda: Group.objects.get(id=group_id))()
        context.user_data["group"] = group
        context.user_data["is_general"] = False
    else:
        context.user_data["group"] = None
        context.user_data["is_general"] = True

    await query.message.reply_text(
        "Now, send the notification message (text, photo, etc.)."
    )
    return raya.states.RECEIVE_NOTIFICATION_MESSAGE


async def receive_notification_message(update: Update, context: CallbackContext):
    message = update.message
    group = context.user_data.get("group")
    is_general = context.user_data["is_general"]

    forwarded_message = await context.bot.forward_message(
        chat_id=settings.HEALTHCHECK_CHAT_ID,
        from_chat_id=update.effective_chat.id,
        message_id=message.message_id,
    )

    notification = await sync_to_async(
        lambda: Notification.objects.create(
            message_id=str(forwarded_message.message_id),
            source_channel_id=settings.HEALTHCHECK_CHAT_ID,
            group=group,
            is_general=is_general,
        )
    )()

    context.user_data["notification_id"] = notification.id

    await update.message.reply_text(
        "Please enter the time to send the notification (e.g., '2025-04-20 15:30')."
        f"⏳ Now: {timezone.now()}"
    )
    return raya.states.RECEIVE_SCHEDULE_TIME


async def receive_schedule_time(update: Update, context: CallbackContext):
    try:
        scheduled_time = parse(update.message.text)
        if scheduled_time < timezone.now():
            await update.message.reply_text(
                "❗ You cannot schedule a notification in the past."
            )
            return raya.states.RECEIVE_SCHEDULE_TIME

        context.user_data["scheduled_time"] = scheduled_time

        await update.message.reply_text(
            f"Notification scheduled for {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')}. Do you confirm?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✅ Confirm", callback_data="confirm_schedule"
                        ),
                        InlineKeyboardButton(
                            "❌ Cancel", callback_data="cancel_schedule"
                        ),
                    ]
                ]
            ),
        )
        return raya.states.CONFIRM_SCHEDULE
    except Exception as e:
        await update.message.reply_text("❗ Invalid time format. Please try again.")
        return raya.states.RECEIVE_SCHEDULE_TIME


async def confirm_schedule(update: Update, context: CallbackContext):
    notification_id = context.user_data["notification_id"]
    scheduled_time = context.user_data["scheduled_time"]

    raya.tasks.send_notification_task.apply_async(
        args=[notification_id], eta=scheduled_time
    )

    await update.message.reply_text(f"✅ Notification scheduled for {scheduled_time}.")
    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext):
    await update.message.reply_text(persian.CANCEL_CONVERSATION)
    return ConversationHandler.END


async def check_private_and_manager(update: Update, context: CallbackContext):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type.upper() != "PRIVATE":
        await update.message.reply_text("⚠️ Please use this command in a private chat.")
        return ConversationHandler.END

    telegram_user = await db_sync_services.get_telegram_user_by_id(user.id)

    if (
        telegram_user is None
        or not telegram_user.is_authorized
        or telegram_user.user_type != TelegramUser.MANAGER_USER
    ):
        await update.message.reply_text(
            "🚫 You are not authorized to perform this action."
        )
        return ConversationHandler.END

    context.user_data["telegram_user"] = telegram_user
    return None
