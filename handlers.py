import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler
from drive_service import get_drive_service, create_document_and_share_with_user
from db import has_user_created_in_folder, update_user_document
from config import get_config
import re

ASK_EMAIL, CONFIRM_CREATION = range(2)
logger = logging.getLogger(__name__)

async def start(update, context):
    await update.message.reply_text("به ربات خوش آمدید! از دستور /send_text برای ایجاد یک سند جدید استفاده کنید.")

async def help_command(update, context):
    await update.message.reply_text("""
        راهنمای استفاده از ربات:
        
        1. با دستور /send_text سندی جدید ایجاد کنید.
        2. پوشه‌ای که می‌خواهید سند در آن ایجاد شود را انتخاب کنید.
        3. آدرس Gmail خود را وارد کنید تا سند به اشتراک گذاشته شود.
        4. سند شما ایجاد و لینک ویرایش آن برای شما ارسال خواهد شد.
    """)

async def send_text(update, context):
    try:
        drive_service = get_drive_service()
        ongoing_folder = get_config()['GOOGLE.DRIVE']['ONGOING_FOLDER_ID']
        results = drive_service.files().list(
            q=f"mimeType='application/vnd.google-apps.folder' and '{ongoing_folder}' in parents",
            spaces='drive',
            fields="files(id, name)"
        ).execute()

        folders = results.get('files', [])
        if not folders:
            await update.message.reply_text('هیچ پوشه‌ای یافت نشد. لطفا دوباره تلاش کنید.')
            return

        keyboard = [[InlineKeyboardButton(folder['name'], callback_data=folder['id'])] for folder in folders]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفا یک پوشه انتخاب کنید تا سند جدید ایجاد شود:', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error during folder listing: {e}")
        await update.message.reply_text("خطایی در بازیابی پوشه‌ها رخ داده است. لطفا دوباره تلاش کنید.")

async def folder_selected(update, context):
    query = update.callback_query
    await query.answer()

    selected_folder_id = query.data
    context.user_data['selected_folder_id'] = selected_folder_id
    await query.message.reply_text('لطفا آدرس Gmail خود را وارد کنید:')
    return ASK_EMAIL

async def ask_email(update, context):
    user_email = update.message.text
    context.user_data['user_email'] = user_email

    if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', user_email):
        await update.message.reply_text('آدرس Gmail نامعتبر است. لطفا یک آدرس معتبر وارد کنید:')
        return ASK_EMAIL

    await update.message.reply_text("سپاس.\n"
                                    "برای تایید ایجاد سند، عبارت **درود بر رایا** را تایپ کنید.")
    logger.info(f"Creating document for email: {user_email}")
    return CONFIRM_CREATION

async def confirm_creation(update, context):
    try:
        if update.message.text != 'درود بر رایا':
            await update.message.reply_text("عبارت تاییدی اشتباه است. لطفا دوباره تلاش کنید.")
            return CONFIRM_CREATION
        user_email = context.user_data['user_email']
        selected_folder_id = context.user_data['selected_folder_id']
        user_id = update.message.from_user.id

        existing_document = has_user_created_in_folder(user_id, selected_folder_id)
        
        if existing_document:
            document_id = existing_document[0]
            drive_service = get_drive_service()

            try:
                result = drive_service.files().get(fileId=document_id, fields="id").execute()
                if result:
                    await update.message.reply_text("شما قبلا یک سند در این پوشه ایجاد کرده‌اید و هنوز در دسترس است!")
                    return ConversationHandler.END
                else:
                    logger.warning(f"Document {document_id} no longer exists")
                    await update.message.reply_text("سند قبلی شما در این پوشه حذف شده است. در حال ایجاد سند جدید...")

            except Exception as e:
                logger.warning(f"Document {document_id} no longer exists: {e}")
                await update.message.reply_text("سند قبلی شما در این پوشه حذف شده است. در حال ایجاد سند جدید...")
        
        doc_id = await create_document_and_share_with_user(update, user_email, selected_folder_id)

        update_user_document(user_id, selected_folder_id, doc_id)

        await update.message.reply_text(f"سند جدید با موفقیت ایجاد و با {user_email} به اشتراک گذاشته شد.\n"
                                        f"لینک ویرایش: https://docs.google.com/document/d/{doc_id}/edit")
    except Exception as e:
        logger.error(f"Error during document creation: {e}")
        await update.message.reply_text("خطایی در ایجاد سند رخ داده است. لطفا دوباره تلاش کنید.")
    return ConversationHandler.END
