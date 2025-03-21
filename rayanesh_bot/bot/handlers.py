import logging
import re
from telegram import Update
from telegram.ext import CallbackContext

from django.conf import settings

from user.models import TelegramUser

logger = logging.getLogger(__name__)

async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    telegram_user, created = TelegramUser.objects.get_or_create(
        telegram_id=user.id,
        defaults={'username': user.username},
    )

    if created:
        await update.message.reply_text(
            f"Welcome to the Rayanesh bot, {user.username}!\n"
        )
    else:
        await update.message.reply_text(f"You're already registered, {telegram_user.name or telegram_user.username}!")
    
async def join_group(update: Update, context: CallbackContext) -> None:
    print(f"Join Message: {update.message.text}")
    await update.message.reply_text("Sent your request!")
    
EMAIL_REGEX = r"[^@]+@[^@]+\.[^@]+"

async def authorize(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    telegram_user = TelegramUser.objects.filter(telegram_id=user.id).first()

    if not telegram_user:
        await update.message.reply_text("⚠️ Please send /start first.")
        return
    
    if not telegram_user.name:
        await update.message.reply_text("Please send your full name (first and last name).")
        telegram_user.state = 'awaiting_name'
        telegram_user.save()
        return

    if not telegram_user.email:
        await update.message.reply_text("Please send your email to continue.")
        telegram_user.state = 'awaiting_email'
        telegram_user.save()
        return

    telegram_user.is_authorized = True
    telegram_user.save()
    await update.message.reply_text(f"✅ Successfully authorized, {telegram_user.name}!")

async def handle_name(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    telegram_user = TelegramUser.objects.filter(telegram_id=user.id).first()

    if not telegram_user or telegram_user.state != 'awaiting_name':
        return

    telegram_user.name = update.message.text.strip()
    telegram_user.state = 'awaiting_email'
    telegram_user.save()

    await update.message.reply_text("Got it! Now, please provide your email.")
    
async def handle_email(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    telegram_user = TelegramUser.objects.filter(telegram_id=user.id).first()

    if not telegram_user or telegram_user.state != 'awaiting_email':
        return

    email = update.message.text.strip()

    if not re.match(EMAIL_REGEX, email):
        await update.message.reply_text("⚠️ That doesn't look like a valid email. Try again.")
        return

    telegram_user.email = email
    telegram_user.is_authorized = True
    telegram_user.state = None
    telegram_user.save()

    await update.message.reply_text(f"✅ Successfully authorized, {telegram_user.name}!")
