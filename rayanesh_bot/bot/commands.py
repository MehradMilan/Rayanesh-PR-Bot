import logging
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext
from user.models import TelegramUser
from document.tasks import create_and_share_document, finalize_document_task
from document.models import Document
from django.conf import settings

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome to the Rayanesh bot! Please send your email to start.')

def register_user(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    telegram_user, created = TelegramUser.objects.get_or_create(
        telegram_id=user.id,
        defaults={'username': user.username, 'first_name': user.first_name},
    )

    if created:
        update.message.reply_text('You have been successfully registered!')
    else:
        update.message.reply_text('You are already registered.')

def create_document(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    telegram_user = TelegramUser.objects.get(telegram_id=user.id)

    doc_code = '123456'
    folder_id = 'some-folder-id'

    create_and_share_document.delay(telegram_user.id, folder_id, doc_code)

    update.message.reply_text('Document creation started!')

def finalize_document(update: Update, context: CallbackContext) -> None:
    doc_code = context.args[0]
    finalize_document_task.delay(doc_code)
    update.message.reply_text(f"Document {doc_code} finalization started.")