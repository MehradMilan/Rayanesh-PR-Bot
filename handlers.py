import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ConversationHandler
from drive_service import (
    get_drive_service,
    create_document_and_share_with_user,
    finalize_document,
    create_document_with_text,
    get_folder_name,
    edit_document_text,
    notify_group,
    get_document_name_by_id
)
from db import has_user_created_in_folder, update_user_document, get_document_id_by_doc_code, delete_doc_by_code
from config import get_config
import re
import random

ASK_EMAIL, ASK_ANON_TEXT, EDIT_ANON_CODE, EDIT_ANON_TEXT, CONFIRM_FINISH, CONFIRM_CREATION = range(6)
logger = logging.getLogger(__name__)

async def start(update, context):
    await update.message.reply_text("به ربات خوش آمدید! از دستور /send_text برای ایجاد یک سند جدید استفاده کنید.")

async def help_command(update, context):
    await update.message.reply_text("""
        با استفاده از این بات، شما می‌توانید متن‌های خود را به‌صورت شناس یا ناشناس به‌دست هیئت تحریریه‌ی رایانش برسانید.
        تنها هیئت تحریریه، ویراستاران و شما به متن ارسالیتان دسترسی خواهند داشت.
                                    
        مراحل ارسال متن به‌صورت شناس:
        🔸 ارسال متن جدید: با اسفاده از دستور /send_text متن جدید خود را ارسال کنید.
            پس از وارد کردن این دستور و انتخاب پوشه‌ی مربوط به شماره‌ی مورد نظرتان، از شما آدرس Gmail خواسته خواهد شد.
            از این آدرس برای افزودن دسترسی سند ایجادشده استفاده خواهد شد.
            
            لطفا پس از پایان تغییرات مدنظرتان، از دستور /finish_text برای اتمام نگارش متن استفاده کنید.
            متن شما پیش از استفاده از این دستور و نهایی شدن آن، در دسترس هیئت تحریریه قرار نمی‌گیرد.

        مراحل ارسال متن به‌صورت ناشناس:
        🔹 ارسال متن ناشناس: با استفاده از دستور /send_text_anon متن ناشناس خود را ارسال کنید.
            پس از انتخاب پوشه‌ی مربوط به شماره‌ی مورد نظرتان، متن شما به‌صورت ناشناس در سندی ایجاد خواهد شد.
            پس از ایجاد سند، یک کد ۶ رقمی به شما اختصاص داده خواهد شد که با استفاده از آن می‌توانید متن خود را ویرایش کنید.
            
            برای ویرایش متن ناشناس خود، از دستور /edit_text_anon استفاده کنید.
            پس از اتمام تغییرات، از دستور /finish_text برای اتمام نگارش متن استفاده کنید.                            
            متن شما پیش از استفاده از این دستور و نهایی شدن آن، در دسترس هیئت تحریریه قرار نمی‌گیرد.
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
            return ConversationHandler.END

        keyboard = [[InlineKeyboardButton(folder['name'], callback_data=f"send_text|{folder['id']}")] for folder in folders]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفا یک پوشه انتخاب کنید تا سند جدید ایجاد شود:', reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error during folder listing: {e}")
        await update.message.reply_text("خطایی در بازیابی پوشه‌ها رخ داده است. لطفا دوباره تلاش کنید.")
        return ConversationHandler.END

async def folder_selected(update, context):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("send_text|"):
        return

    selected_folder_id = query.data.split('|')[1]
    context.user_data['selected_folder_id'] = selected_folder_id
    await query.message.reply_text('لطفا آدرس Gmail خود را وارد کنید:')
    return ASK_EMAIL

async def ask_email(update, context):
    user_email = update.message.text
    context.user_data['user_email'] = user_email

    if not re.match(r'^[a-zA-Z0-9._%+-]+@gmail\.com$', user_email):
        await update.message.reply_text('آدرس Gmail نامعتبر است. لطفا یک آدرس معتبر وارد کنید:')
        return ASK_EMAIL

    await update.message.reply_text(text='سپاس.\n'
                                    'برای تایید ایجاد سند، عبارت «تایید» را تایپ کنید.')
    logger.info(f"Creating document for email: {user_email}")
    return CONFIRM_CREATION

async def confirm_creation(update, context):
    try:
        if update.message.text != 'تایید':
            await update.message.reply_text("عبارتی که وارد کرده‌اید اشتباه است. لطفا دوباره تلاش کنید.")
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
        
        doc_code = generate_code()
        doc_id = await create_document_and_share_with_user(update, user_email, selected_folder_id, doc_code)
        update_user_document(user_id, selected_folder_id, doc_id, doc_code)

        await update.message.reply_text(f"سند جدید با موفقیت ایجاد و با {user_email} به اشتراک گذاشته شد.\n"
                                        f"لینک ویرایش: https://docs.google.com/document/d/{doc_id}/edit\n\n"
                                        f"کد سندی که برای شما ایجاد‌شده است: {doc_code}\n"
                                        f"هر گاه نگارش سند به پایان رسید، با استفاده از دستور پایان نگارش و ارائه‌ی این کد، می‌توانید سند را نهایی کنید.\n"
                                        f"سپس هیئت تحریریه متن شما را بررسی کرده و به شما مراحل بعدی را اطلاع می‌دهیم.")
    except Exception as e:
        logger.error(f"Error during document creation: {e}")
        await update.message.reply_text("خطایی در ایجاد سند رخ داده است. لطفا دوباره تلاش کنید.")
    return ConversationHandler.END

def generate_code():
    return str(random.randint(100000, 999999))

async def send_text_anon(update, context):
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
            return ConversationHandler.END

        keyboard = [[InlineKeyboardButton(folder['name'], callback_data=f"send_text_anon|{folder['id']}")] for folder in folders]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفا یک پوشه انتخاب کنید تا متن ناشناس خود را ثبت کنید:', reply_markup=reply_markup)
        return ASK_ANON_TEXT

    except Exception as e:
        logger.error(f"Error during folder listing: {e}")
        await update.message.reply_text("خطایی در بازیابی پوشه‌ها رخ داده است. لطفا دوباره تلاش کنید.")
        return ConversationHandler.END

async def ask_anon_text(update, context):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("send_text_anon|"):
        return

    selected_folder_id = query.data.split('|')[1]
    context.user_data['selected_folder_id'] = selected_folder_id
    await query.message.reply_text('🔸لطفا متن ناشناس خود را در قالب یک پیام ارسال کنید:\n'
                                   '🔹متن شما به‌صورت ناشناس در سند ثبت خواهد شد.\n'
                                   '🔸اگر طول متن شما بیش از یک پیام است، می‌توانید آن را در یک بستر عمومی قرارداده و لینک آن را در این‌جا ارسال کنید.\n')
    return ASK_ANON_TEXT

async def receive_anon_text(update, context):
    user_text = update.message.text
    selected_folder_id = context.user_data['selected_folder_id']
    
    code = generate_code()
    folder_name = get_folder_name(selected_folder_id)
    doc_title = f"Anon-{folder_name}-{code}"

    try:
        doc_id = await create_document_with_text(doc_title, selected_folder_id, user_text)
        await update.message.reply_text(
            f"🔸متن شما ثبت شد.\n"
            f"🔹کد سندی که برای شما ایجاد‌شده است: {code}\n"
            f"🔸هر گاه نگارش سند به پایان رسید، با استفاده از دستور پایان نگارش و ارائه‌ی این کد، می‌توانید سند را نهایی کنید.\n"
            f"🔹سپس هیئت تحریریه متن شما را بررسی کرده و به شما مراحل بعدی را اطلاع می‌دهیم.\n"
            f"🔸پیش از نهایی شدن، می‌توانید با استفاده از کدی که در اختیار دارید، سند خود را تغییر دهید.")
    except Exception as e:
        logger.error(f"Error creating anonymous document: {e}")
        await update.message.reply_text("خطایی در ایجاد سند رخ داده است. لطفا دوباره تلاش کنید.")

    return ConversationHandler.END

async def edit_text_anon(update, context):
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
            return ConversationHandler.END

        keyboard = [[InlineKeyboardButton(folder['name'], callback_data=f"edit_text_anon|{folder['id']}")] for folder in folders]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('لطفا پوشه‌ای که متن شما در آن قرار دارد انتخاب کنید تا متن ناشناس خود را تغییر دهید:', reply_markup=reply_markup)
        return EDIT_ANON_CODE

    except Exception as e:
        logger.error(f"Error during folder listing: {e}")
        await update.message.reply_text("خطایی در بازیابی پوشه‌ها رخ داده است. لطفا دوباره تلاش کنید.")
        return ConversationHandler.END

async def ask_anon_edit_code(update, context):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("edit_text_anon|"):
        return

    selected_folder_id = query.data.split('|')[1]
    context.user_data['selected_folder_id'] = selected_folder_id

    await query.message.reply_text("لطفا کد ۶ رقمی متن خود را وارد کنید:")
    return EDIT_ANON_CODE

async def confirm_edit(update, context):
    user_text = update.message.text
    folder_id = context.user_data['selected_folder_id']

    code = user_text
    context.user_data['code'] = code

    drive_service = get_drive_service()

    try:
        results = drive_service.files().list(
            q=f"name contains '{code}' and '{folder_id}' in parents",
            spaces='drive',
            fields="files(id, name)"
        ).execute()
        print(results)
        files = results.get('files', [])
        if files:
            doc_id = files[0]['id']
            context.user_data['doc_id'] = doc_id
            await update.message.reply_text('لطفا متن جدید خود را ارسال کنید:')
            return EDIT_ANON_TEXT
        else:
            await update.message.reply_text('هیچ سندی با این کد یافت نشد.')
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error during document search: {e}")
        await update.message.reply_text("خطایی رخ داده است. لطفا دوباره تلاش کنید.")
        return ConversationHandler.END

async def update_anon_text(update, context):
    new_text = update.message.text
    doc_id = context.user_data['doc_id']
    
    await edit_document_text(doc_id, new_text)
    await update.message.reply_text("متن شما با موفقیت به‌روزرسانی شد.")
    return ConversationHandler.END

async def finish_text(update, context):
    await update.message.reply_text("لطفا کد ۶ رقمی متن خود را وارد کنید:")
    return CONFIRM_FINISH

async def confirm_finish(update, context):
    code = update.message.text.strip()
    
    doc_id = get_document_id_by_doc_code(code)
    
    if doc_id:
        context.user_data['code'] = code
        doc_name = await get_document_name_by_id(doc_id)
        delete_doc_by_code(code)
    else:
        drive_service = get_drive_service()
        try:
            results = drive_service.files().list(
                q=f"name contains '{code}'",
                spaces='drive',
                fields="files(id, name)"
            ).execute()

            files = results.get('files', [])
            if files:
                doc_id = files[0]['id']
                doc_name = files[0]['name']
            else:
                await update.message.reply_text("هیچ سندی با این کد یافت نشد.")
                return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error during document search: {e}")
            await update.message.reply_text("خطایی رخ داده است. لطفا دوباره تلاش کنید.")
            return ConversationHandler.END
        
    try:
        final_name = await finalize_document(doc_id, doc_name)
        await update.message.reply_text(f"سند شما نهایی شد.")
        await notify_group(final_name, doc_id)
    except Exception as e:
        logger.error(f"Error finalizing document: {e}")
        await update.message.reply_text("خطایی در نهایی‌سازی سند رخ داده است.")
    
    return ConversationHandler.END
