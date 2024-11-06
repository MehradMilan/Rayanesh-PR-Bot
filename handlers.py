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
    get_document_name_by_id,
)
from db import (
    has_user_created_in_folder,
    update_user_document,
    get_document_id_by_doc_code,
    delete_doc_by_code,
)
from config import get_config
import re
import random
from init import get_application
import requests
from constants import POETS_GANJOOR
from constants import (
    ASK_EMAIL,
    CONFIRM_CREATION,
    ASK_ANON_TEXT,
    EDIT_ANON_CODE,
    EDIT_ANON_TEXT,
    CONFIRM_FINISH,
    FEEDBACK_TEXT,
    POET_TEXT,
    SUGGEST_MOVIE,
)

logger = logging.getLogger(__name__)


async def start(update, context):
    await update.message.reply_text(
        """
                                    درود!
به بات رایانش خوش اومدی❤️

🔹 کاربری بات
▫️ در حال حاضر، می‌تونی نوشته‌هایی که دوست داری در شماره‌ها یا هر بستر دیگه‌ای از سمت رایانش منتشر بشه رو به‌راحتی برامون بفرستی و به‌دست هیئت تحریریه برسونی. این کار رو می‌تونی به‌صورت شناس یا ناشناس انجام بدی.
▫️ از شنیدن انتقاد، نظر و خصوصا پیشنهاد شما هم همیشه خوشحال می‌شیم :)

🔸 دم‌دستی ولی متن‌باز!
▫️این بات رو کوچولو و دم‌دستی بالا آوردیم که یه ساز و کاری برای جمع‌آوری متن‌ها داشته باشیم. راستی گزارش مشکل و باگ رو فراموش نکن.
▫️خب کدش عمومیه و هر وقت خواستی کانتریبیشونی(!) به پروژه داشته باشی، باگی رو رفع کنی، یا ایده‌ی جدیدی رو پیاده‌سازی کنی، حتما بهمون پیام بده!

🔹 چگونه؟
▫️ کارکرد بات خیلی راحته! هم می‌تونی از دستور /help کمک بگیری و هم هروقت مشکلی پیش اومد با سردبیر در ارتباط باش.

سپاس از بودنت.
🟢 رایانش
                                    """
    )


async def help_command(update, context):
    await update.message.reply_text(
        """
🔸 با استفاده از این بات، شما می‌توانید متن‌های خود را به‌صورت شناس یا ناشناس به‌دست هیئت تحریریه‌ی رایانش برسانید.
🔹 تنها هیئت تحریریه، ویراستاران و شما به متن ارسالیتان دسترسی خواهند داشت.
                                    
🔸 همچنین می‌توانید انتقاد، نظر و پیشنهادتان را به‌راحتی برای ما با استفاده از دستور /feedback ارسال کنید.
                                    
🔹 دستور /random_poem یک شعر رندوم را برایتان ارسال می‌کند. :)
                                    
🔸 با دستور /select_poet می‌توانید شاعر موردنظرتان را انتخاب کرده و یک شعر از او دریافت کنید.


🟠 مراحل ارسال متن به‌صورت شناس

▫️ با اسفاده از دستور /send_text متن جدید خود را ارسال کنید.
◾️ پس از وارد کردن این دستور و انتخاب پوشه‌ی مربوط به شماره‌ی مورد نظرتان، از شما آدرس Gmail خواسته خواهد شد. از این آدرس برای افزودن دسترسی سند ایجادشده استفاده خواهد شد.
▫️ لینک یک سند که در گوگل‌درایو رایانش ایجاد شده، برای شما ارسال می‌شود. لطفا طبق قواعدی که در سند نوشته شده، متن خود را وارد کنید.
◾️ پس از پایان تغییرات مدنظرتان، از دستور /finish_text برای اتمام نگارش متن استفاده کنید. متن شما پیش از استفاده از این دستور و نهایی شدن آن، در دسترس هیئت تحریریه قرار نمی‌گیرد.


🔵 مراحل ارسال متن به‌صورت ناشناس

▫️ با استفاده از دستور /send_text_anon متن ناشناس خود را ارسال کنید.
◾️ پس از انتخاب پوشه‌ی مربوط به شماره‌ی مورد نظرتان، متن شما به‌صورت ناشناس در سندی ایجاد خواهد شد.
▫️ پس از ایجاد سند، یک کد ۶ رقمی به شما اختصاص داده خواهد شد که با استفاده از آن می‌توانید متن خود را ویرایش کنید.
◾️ برای ویرایش متن ناشناس خود، از دستور /edit_text_anon استفاده کنید.
▫️ پس از اتمام تغییرات، از دستور /finish_text برای اتمام نگارش متن استفاده کنید.
◾️ متن شما پیش از استفاده از این دستور و نهایی شدن آن، در دسترس هیئت تحریریه قرار نمی‌گیرد.
    """
    )


async def send_text(update, context):
    try:
        drive_service = get_drive_service()
        ongoing_folder = get_config()["GOOGLE.DRIVE"]["ONGOING_FOLDER_ID"]
        results = (
            drive_service.files()
            .list(
                q=f"mimeType='application/vnd.google-apps.folder' and '{ongoing_folder}' in parents",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )

        folders = results.get("files", [])
        if not folders:
            await update.message.reply_text(
                """
🔴 هیچ پوشه‌ای یافت نشد.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
            )
            return ConversationHandler.END

        keyboard = [
            [
                InlineKeyboardButton(
                    folder["name"], callback_data=f"send_text|{folder['id']}"
                )
            ]
            for folder in folders
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            """
🔸 لیست شماره‌هایی که الان می‌توانید برای آن‌ها متن ارسال کنید در زیر آورده‌شده‌است.

🔹 پوشه‌ی مربوط به شماره‌ی مدنظرتان را انتخاب کنید.
🔻پوشه‌ی «No Category» برای نوشته‌هاییست که از بستر انتشار آن مطمئن نیستید و فقط می‌خواهید ارسال کنید!
                                        """,
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Error during folder listing: {e}")
        await update.message.reply_text(
            """
🔴 خطایی در بازیابی پوشه‌ها رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
        )
        return ConversationHandler.END


async def folder_selected(update, context):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("send_text|"):
        return

    selected_folder_id = query.data.split("|")[1]
    context.user_data["selected_folder_id"] = selected_folder_id
    await query.edit_message_text(
        """
🔸 لطفا آدرس Gmail خود را وارد کنید:

🔹 از این آدرس برای اجازه‌ی دسترسی به سند ساخته‌شده استفاده می‌شود.
"""
    )
    return ASK_EMAIL


async def ask_email(update, context):
    user_email = update.message.text
    context.user_data["user_email"] = user_email

    if not re.match(r"^[a-zA-Z0-9._%+-]+@gmail\.com$", user_email):
        await update.message.reply_text(
            """
🔴 آدرس Gmail نامعتبر است.

🔸لطفا یک آدرس معتبر وارد کنید:
"""
        )
        return ASK_EMAIL

    await update.message.reply_text(
        text=""""
🔹 سپاسگزارم. در ادامه سند شما در پوشه‌ی مربوط به شماره‌ای که انتخاب کرده‌اید، ایجاد شده و در دسترس شما قرار می‌گیرد.

🔸 برای تایید ایجاد سند، کلمه‌ی «تایید» را ارسال کنید.
                                    """
    )
    logger.info(f"Creating document for email: {user_email}")
    return CONFIRM_CREATION


async def confirm_creation(update, context):
    try:
        if update.message.text != "تایید":
            await update.message.reply_text(
                """
🔴 عبارتی که وارد کرده‌اید اشتباه است.

🔸 لطفا دوباره تلاش کنید.
🔹 دقیقا کلمه‌ی «تایید» را بدون اضافه یا کم ارسال کنید.
"""
            )
            return CONFIRM_CREATION
        user_email = context.user_data["user_email"]
        selected_folder_id = context.user_data["selected_folder_id"]
        user_id = update.message.from_user.id

        no_category_id = get_config()["GOOGLE.DRIVE"]["NOCATEGORY_FOLDER_ID"]

        existing_document = has_user_created_in_folder(user_id, selected_folder_id)

        if existing_document and selected_folder_id != no_category_id:
            document_id = existing_document[0]
            drive_service = get_drive_service()

            try:
                result = (
                    drive_service.files().get(fileId=document_id, fields="id").execute()
                )
                if result:
                    await update.message.reply_text(
                        f"""
🔴 این پوشه محدودیت تعداد متن ارسالی همزمان از سوی کاربران دارد.
🔻 شما قبلا یک سند در این پوشه ایجاد کرده‌اید و هنوز در دسترس است!

🔸 لینک ویرایش:
🔗 https://docs.google.com/document/d/{document_id}/edit

🔹می‌توانید متن قبلی خود را نهایی کنید یا به اطلاع سردبیر برسانید.
"""
                    )
                    return ConversationHandler.END
                else:
                    logger.warning(f"Document {document_id} no longer exists")
                    await update.message.reply_text(
                        """
🟡 سند قبلی شما در این پوشه جابجا یا حذف شده است.

🔹در حال ایجاد سند جدید برای شما ...
"""
                    )

            except Exception as e:
                logger.warning(f"Document {document_id} no longer exists: {e}")
                await update.message.reply_text(
                    """
🟡 سند قبلی شما در این پوشه جابجا یا حذف شده است.

🔹در حال ایجاد سند جدید برای شما ...
"""
                )

        doc_code = generate_code()
        doc_id = await create_document_and_share_with_user(
            update, user_email, selected_folder_id, doc_code
        )
        update_user_document(user_id, selected_folder_id, doc_id, doc_code)

        await update.message.reply_text(
            f"""
🟢 یک سند جدید با موفقیت ایجاد و با {user_email} به اشتراک گذاشته شد.

🔹لینک ویرایش:
🔗 https://docs.google.com/document/d/{doc_id}/edit

🔸 کد سند ایجاد‌شده: {doc_code}
🔻 هر گاه نگارش سند به پایان رسید، با استفاده از دستور پایان نگارش و ارائه‌ی این کد، می‌توانید سند را نهایی کنید.

🔹 سپس هیئت تحریریه متن شما را بررسی کرده و به شما مراحل بعدی را از طریق ایمیل اطلاع می‌دهیم.
🔻 اگر مایل هستید ارتباط از طریق تلگرام باشد، نام و آیدی خود را در مکان مشخص‌شده در سند قرار دهید.

🔸 لطفا طبق قواعدی که در سند نوشته شده، متن خود را وارد کنید.

🟢 رایانش
"""
        )
    except Exception as e:
        logger.error(f"Error during document creation: {e}")
        await update.message.reply_text(
            """
🔴 خطایی در ایجاد سند رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
        )
    return ConversationHandler.END


def generate_code():
    return str(random.randint(100000, 999999))


async def send_text_anon(update, context):
    try:
        drive_service = get_drive_service()
        ongoing_folder = get_config()["GOOGLE.DRIVE"]["ONGOING_FOLDER_ID"]
        results = (
            drive_service.files()
            .list(
                q=f"mimeType='application/vnd.google-apps.folder' and '{ongoing_folder}' in parents",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )

        folders = results.get("files", [])
        if not folders:
            await update.message.reply_text(
                """
🔴 هیچ پوشه‌ای یافت نشد.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
            )
            return ConversationHandler.END

        keyboard = [
            [
                InlineKeyboardButton(
                    folder["name"], callback_data=f"send_text_anon|{folder['id']}"
                )
            ]
            for folder in folders
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            """
🔸 لیست شماره‌هایی که الان می‌توانید برای آن‌ها متن ناشناس ارسال کنید در زیر آورده‌شده‌است.

🔹 پوشه‌ی مربوط به شماره‌ی مدنظرتان را انتخاب کنید.
🔻پوشه‌ی «No Category» برای نوشته‌هاییست که از بستر انتشار آن مطمئن نیستید و فقط می‌خواهید ارسال کنید!
                                        """,
            reply_markup=reply_markup,
        )
        return ASK_ANON_TEXT

    except Exception as e:
        logger.error(f"Error during folder listing: {e}")
        await update.message.reply_text(
            """
🔴 خطایی در بازیابی پوشه‌ها رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
        )
        return ConversationHandler.END


async def ask_anon_text(update, context):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("send_text_anon|"):
        return

    selected_folder_id = query.data.split("|")[1]
    context.user_data["selected_folder_id"] = selected_folder_id
    await query.edit_message_text(
        """
🔸لطفا متن ناشناس خود را در قالب یک پیام ارسال کنید.
🔻 اگر طول متن شما بیش از یک پیام است، می‌توانید آن را در یک بستر عمومی قرارداده و لینک آن را در این‌جا ارسال کنید.

🔹متن شما به‌صورت ناشناس در سند ثبت خواهد شد.

🔸 پس از ایجاد سند، یک کد ۶ رقمی به شما اختصاص داده خواهد شد که با استفاده از آن می‌توانید متن خود را ویرایش و نهایی کنید.
🔻 برای ویرایش متن ناشناس خود، از دستور /edit_text_anon استفاده کنید.

"""
    )
    return ASK_ANON_TEXT


async def receive_anon_text(update, context):
    user_text = update.message.text
    selected_folder_id = context.user_data["selected_folder_id"]

    code = generate_code()
    folder_name = get_folder_name(selected_folder_id)
    doc_title = f"Anon-{folder_name}-{code}"

    try:
        doc_id = await create_document_with_text(
            doc_title, selected_folder_id, user_text
        )
        await update.message.reply_text(
            f"""
🟢 متن شما ثبت شد. از ارسال نوشته‌تان سپاسگزاریم :)

🔸 کد سند ایجاد‌شده: {code}
🔻 هر گاه نگارش سند به پایان رسید، با استفاده از دستور پایان نگارش و ارائه‌ی این کد، می‌توانید سند را نهایی کنید.

🔹 سپس هیئت تحریریه متن شما را بررسی کرده و به شما مراحل بعدی را از طریق ایمیل اطلاع می‌دهیم.

🔸پیش از نهایی شدن، می‌توانید با استفاده از دستور /edit_text_anon و کدی که در اختیار دارید، سند خود را تغییر دهید.

🟢 رایانش
"""
        )
    except Exception as e:
        logger.error(f"Error creating anonymous document: {e}")
        await update.message.reply_text(
            """
🔴 خطایی در ایجاد سند رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
        )

    return ConversationHandler.END


async def edit_text_anon(update, context):
    try:
        drive_service = get_drive_service()
        ongoing_folder = get_config()["GOOGLE.DRIVE"]["ONGOING_FOLDER_ID"]
        results = (
            drive_service.files()
            .list(
                q=f"mimeType='application/vnd.google-apps.folder' and '{ongoing_folder}' in parents",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )

        folders = results.get("files", [])
        if not folders:
            await update.message.reply_text(
                """
🔴 هیچ پوشه‌ای یافت نشد.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
            )
            return ConversationHandler.END

        keyboard = [
            [
                InlineKeyboardButton(
                    folder["name"], callback_data=f"edit_text_anon|{folder['id']}"
                )
            ]
            for folder in folders
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            """
🔸 لطفا پوشه‌ای که متن شما در آن قرار دارد انتخاب کنید تا متن ناشناس خود را تغییر دهید:
""",
            reply_markup=reply_markup,
        )
        return EDIT_ANON_CODE

    except Exception as e:
        logger.error(f"Error during folder listing: {e}")
        await update.message.reply_text(
            """
🔴 خطایی در بازیابی پوشه‌ها رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
        )
        return ConversationHandler.END


async def ask_anon_edit_code(update, context):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("edit_text_anon|"):
        return

    selected_folder_id = query.data.split("|")[1]
    context.user_data["selected_folder_id"] = selected_folder_id

    await query.edit_message_text(
        """
🔸 لطفا کد ۶ رقمی متن خود را وارد کنید:

🔹 اگر آن را در اختیار ندارید، می‌توانید با سردبیر در ارتباط باشید.
"""
    )
    return EDIT_ANON_CODE


async def confirm_edit(update, context):
    user_text = update.message.text
    folder_id = context.user_data["selected_folder_id"]

    code = user_text
    context.user_data["code"] = code

    drive_service = get_drive_service()

    try:
        results = (
            drive_service.files()
            .list(
                q=f"name contains '{code}' and '{folder_id}' in parents and not name contains 'FINAL'",
                spaces="drive",
                fields="files(id, name)",
            )
            .execute()
        )
        files = results.get("files", [])
        if files:
            doc_id = files[0]["id"]
            context.user_data["doc_id"] = doc_id
            await update.message.reply_text(
                """
🔸لطفا متن ناشناس جدید خود را در قالب یک پیام ارسال کنید.
🔻 اگر طول متن شما بیش از یک پیام است، می‌توانید آن را در یک بستر عمومی قرارداده و لینک آن را در این‌جا ارسال کنید.

🔹متن شما به‌صورت ناشناس در سند ثبت خواهد شد.
"""
            )
            return EDIT_ANON_TEXT
        else:
            await update.message.reply_text(
                """
🔴 هیچ سندی با این کد یافت نشد.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
            )
            return ConversationHandler.END

    except Exception as e:
        logger.error(f"Error during document search: {e}")
        await update.message.reply_text(
            """
🔴 خطایی در ایجاد سند رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
        )
        return ConversationHandler.END


async def update_anon_text(update, context):
    new_text = update.message.text
    doc_id = context.user_data["doc_id"]

    await edit_document_text(doc_id, new_text)
    await update.message.reply_text(
        """
🟢 متن شما به‌روز رسانی شد. از ارسال نوشته‌تان سپاسگزاریم :)
"""
    )
    return ConversationHandler.END


async def finish_text(update, context):
    await update.message.reply_text(
        """
🔸 لطفا کد ۶ رقمی متن خود را وارد کنید:

🔹 اگر آن را در اختیار ندارید، می‌توانید با سردبیر در ارتباط باشید.
"""
    )
    return CONFIRM_FINISH


async def confirm_finish(update, context):
    code = update.message.text.strip()

    doc_id = get_document_id_by_doc_code(code)

    if doc_id:
        context.user_data["code"] = code
        doc_name = await get_document_name_by_id(doc_id)
        delete_doc_by_code(code)
    else:
        drive_service = get_drive_service()
        try:
            results = (
                drive_service.files()
                .list(
                    q=f"name contains '{code}' and not name contains 'FINAL'",
                    spaces="drive",
                    fields="files(id, name)",
                )
                .execute()
            )

            files = results.get("files", [])
            if files:
                doc_id = files[0]["id"]
                doc_name = files[0]["name"]
            else:
                await update.message.reply_text(
                    """
🔴 هیچ سندی با این کد یافت نشد.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
                )
                return ConversationHandler.END

        except Exception as e:
            logger.error(f"Error during document search: {e}")
            await update.message.reply_text(
                """
🔴 خطایی در بازیابی سند رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
            )
            return ConversationHandler.END

    try:
        final_name = await finalize_document(doc_id, doc_name)
        await update.message.reply_text(
            """
🟢 متن شما نهایی شد. از ارسال نوشته‌تان سپاسگزاریم :)

🔹 نهایی‌شدن متن شما به اطلاع هیئت تحریریه می‌رسد و در سریع‌ترین زمان ممکن بررسی و ویراستاری خواهد شد.

🔺 ارسال متن شما به‌صورت شناس به این معناست که رایانش می‌تواند در بستری که مشخص کرده‌اید، در هر زمانی آن را با نام شما منتشر کند.
🔺 ارسال متن شما به‌صورت ناشناس به این معناست که رایانش می‌تواند در بستری که مشخص کرده‌اید، در هر زمانی آن را با نام «ناشناس» منتشر کند.

🔸 اگر در موارد بالا ایرادی وجود دارد، به اطلاع سردبیر برسانید.

🟢 رایانش
"""
        )
        await notify_group(final_name, doc_id)
    except Exception as e:
        logger.error(f"Error finalizing document: {e}")
        await update.message.reply_text(
            """
🔴 خطایی در نهایی‌سازی سند رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
        )
    return ConversationHandler.END


async def send_random_poem(update, context):
    response = requests.get("https://api.ganjoor.net/api/ganjoor/poem/random")
    if response.status_code == 200:
        poem_data = response.json()
        fullTitle = poem_data.get("fullTitle")
        body = poem_data.get("plainText")
        await update.message.reply_text(
            f"""
🔸 {fullTitle}

🔹 شعر:

{body}

@Rayanesh_CE
        """
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text(
            """
🔴 خطایی در بازیابی شعر رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
        )
        return ConversationHandler.END


async def select_poet(update, context):
    options = POETS_GANJOOR
    keyboard = [
        [InlineKeyboardButton(option, callback_data=f"poet|{option}")]
        for option in options
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        """
🔸 لطفا شاعر مورد نظر خود را انتخاب کنید:
    """,
        reply_markup=reply_markup,
    )
    return POET_TEXT


async def send_poem(update, context):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("poet|"):
        return

    selected_poet = query.data.split("|")[1]
    poetId = POETS_GANJOOR[selected_poet]
    response = requests.get(
        f"https://api.ganjoor.net/api/ganjoor/poem/random?poetId={poetId}"
    )
    if response.status_code == 200:
        poem_data = response.json()
        fullTitle = poem_data.get("fullTitle")
        body = poem_data.get("plainText")
        await query.edit_message_text(
            f"""
🔸 {fullTitle}

🔹 شعر:

{body}

@Rayanesh_CE
        """
        )
        return ConversationHandler.END


async def send_feedback(update, context):
    options = ["پیشنهاد", "انتقاد", "نظر"]
    keyboard = [
        [InlineKeyboardButton(option, callback_data=f"feedback|{option}")]
        for option in options
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        """
🔸 لطفا نوع بازخورد خود را انتخاب کنید:
    """,
        reply_markup=reply_markup,
    )
    return FEEDBACK_TEXT


async def ask_feedback_text(update, context):
    query = update.callback_query
    await query.answer()

    if not query.data.startswith("feedback|"):
        return

    selected_option = query.data.split("|")[1]
    context.user_data["selected_option"] = selected_option
    await query.edit_message_text(
        """
🔸 لطفا بازخورد خود را در قالب یک پیام بنویسید:
                                   
🔹 این بازخورد به‌صورت ناشناس برای اعضای رایانش ارسال خواهد شد.
                                   
🔸 اگر می‌خواهید در ادامه در ارتباط باشیم، نام و آیدی تلگرام خود را در انتهای پیام بنویسید.
"""
    )
    return FEEDBACK_TEXT


async def notify_feedback(selected_option, feedback_text):
    chat_id = get_config()["TELEGRAM.BOT"]["GHALBE_TAPANDEH_ID"]
    bot = get_application().bot
    await bot.send_message(
        chat_id,
        f"""
🔸 نوع بازخورد: #{selected_option}

🔹 بازخورد:

{feedback_text}
    """,
    )
    return


async def receive_feedback_text(update, context):
    feedback_text = update.message.text
    selected_option = context.user_data["selected_option"]

    try:
        await notify_feedback(selected_option, feedback_text)
        await update.message.reply_text(
            """
    🟢 بازخورد شما ثبت شد. از ارسال بازخوردتان سپاسگزاریم :)
    """
        )
    except Exception as e:
        logger.error(f"Error sending feedback: {e}")
        await update.message.reply_text(
            """
🔴 خطایی در ارسال بازخورد رخ داده‌است.
🔻 لطفا دوباره تلاش کنید یا به اطلاع سردبیر برسانید!
"""
        )

    return ConversationHandler.END


async def suggest_movie(update, context):
    logger.info("suggest_movie called")
    await update.message.reply_text(
        """
🔸 لطفا نام فیلم مورد نظرتان را وارد کنید:
"""
    )
    return SUGGEST_MOVIE


async def search_movie_in_imdb(movie_name):
    collect_api_token = get_config()["IMDB.API"]["Token"]
    url = f"https://api.collectapi.com/imdb/imdbSearchByName?query={movie_name}"
    headers = {
        "authorization": f"apikey {collect_api_token}",
        "content-type": "application/json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return None


async def respond_to_movie_suggestion(update, context):
    logger.info("respond_to_movie_suggestion called")
    movie_name = update.message.text
    response = await search_movie_in_imdb(movie_name)
    if response:
        movie_data = response["result"]
        if movie_data:
            movie = movie_data[0]
            title = movie["Title"]
            year = movie["Year"]
            imdb_id = movie["imdbID"]
            type_ = movie["Type"]
            img_url = movie["Poster"]
            await update.message.reply_photo(
                photo=img_url,
                caption=f"""
🔸 نام: {title}
🔹 سال: {year}
🔸 نوع: {type_}
            )
            """,
            )
            await notify_movie_suggestion(movie_name, movie_data)
        else:
            await update.message.reply_text(
                """
فیلم با نام موردنظر در دیتابیس IMDB یافت نشد. نام فیلم مورد نظر شما همچنان به اطلاع تیم برگزار کننده‌ی CENama می‌رسد.
"""
            )
        return ConversationHandler.END


async def notify_movie_suggestion(movie_name, imdb_context):
    chat_id = get_config()["TELEGRAM.BOT"]["GHALBE_TAPANDEH_ID"]
    bot = get_application().bot
    movie = imdb_context[0]
    await bot.send_photo(
        photo=movie["Poster"],
        caption=f"""
        #CENAMA
🔸 نام: {movie["Title"]}
🔹 سال: {movie["Year"]}
🔸 نوع: {movie["Type"]}
            """,
    )
    return
