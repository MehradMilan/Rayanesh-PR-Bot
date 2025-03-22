import logging
import re
from telegram import Update, User
from telegram.ext import CallbackContext

from django.conf import settings

from user.models import TelegramUser
import db_sync_services

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext) -> None:
    user: User = update.effective_user
    telegram_user, created = await db_sync_services.get_or_create_telegram_user(user)
    print(f"created: {created}")
    print(f"telegram_user: {telegram_user}")

    if created:
        await update.message.reply_text(
            f"Welcome to the Rayanesh bot, {user.username}!\n"
        )
    else:
        await update.message.reply_text(
            f"You're already registered, {telegram_user.name or telegram_user.username}!"
        )


async def join_group(update: Update, context: CallbackContext) -> None:
    print(f"Join Message: {update.message.text}")
    await update.message.reply_text("Sent your request!")


EMAIL_REGEX = r"[^@]+@[^@]+\.[^@]+"


async def authorize(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    telegram_user = db_sync_services.get_telegram_user_by_id(user.id)

    if not telegram_user:
        await update.message.reply_text("⚠️ Please send /start first.")
        return

    if not telegram_user.name:
        await update.message.reply_text(
            "Please send your full name (first and last name)."
        )
        telegram_user.state = TelegramUser.AWAITING_NAME_STATE
        db_sync_services.save_user(telegram_user)
        return

    if not telegram_user.email:
        await update.message.reply_text("Please send your email to continue.")
        telegram_user.state = TelegramUser.AWAITING_EMAIL_STATE
        db_sync_services.save_user(telegram_user)
        return

    telegram_user.is_authorized = True
    db_sync_services.save_user(telegram_user)
    await update.message.reply_text(
        f"✅ Successfully authorized, {telegram_user.name}!"
    )


async def handle_name(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    telegram_user = db_sync_services.get_telegram_user_by_id(user.id)

    if not telegram_user or telegram_user.state != TelegramUser.AWAITING_NAME_STATE:
        return

    telegram_user.name = update.message.text.strip()
    telegram_user.state = TelegramUser.AWAITING_EMAIL_STATE
    db_sync_services.save_user(telegram_user)

    await update.message.reply_text("Got it! Now, please provide your email.")


async def handle_email(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    telegram_user = db_sync_services.get_telegram_user_by_id(user.id)

    if not telegram_user or telegram_user.state != TelegramUser.AWAITING_EMAIL_STATE:
        return

    email = update.message.text.strip()

    if not re.match(EMAIL_REGEX, email):
        await update.message.reply_text(
            "⚠️ That doesn't look like a valid email. Try again."
        )
        return

    telegram_user.email = email
    telegram_user.is_authorized = True
    telegram_user.state = None
    db_sync_services.save_user(telegram_user)

    await update.message.reply_text(
        f"✅ Successfully authorized, {telegram_user.name}!"
    )
