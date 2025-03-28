GROUP_NOT_FOUND = """
گروه مد نظر شما پیدا نشد!
"""

USER_UNAUTHORIZED = """
هویت شما احراز نشده‌است!
لطفا از دستور \authorize
استفاده کنید.
"""

GROUP_REQUEST_ALREADY_EXIST = """
شما برای عضویت در این گروه قبلا درخواست داده‌اید!
لطفا تا تایید مسئول گروه صبر کنید.
"""
GROUP_REQUEST_SUCCESS = """
درخواست عضویت شما با موفقیت ارسال شد!
پس از تایید توسط مسئول گروه، به شما پیام‌های بعدی ارسال خواهد شد.
"""

START_SUCCESS = """
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

USER_NOT_EXIST = """
خوش اومدی! لطفا در ابتدا از \start استفاده کن.
"""

ENTER_NAME = """
لطفا اسم خودت رو وارد کن. اگه نام و نام خانوادگیت باشه که اصلا بهتر!
"""

ENTER_EMAIL = """
لطفا آدرس جیمیل خودت رو بنویس. از این آدرس برای دسترسی دادن به درایو و داک‌ها استفاده می‌کنیم. شاید ایمیلم بدیم بعدا!
"""
EMAIL_INVALID = """
هممم، به‌نظر جیمیلت معتبر نیست. یه بار دیگه تست کن. اگر هم مشکلی هست بهمون اطلاع بده!
"""

USER_AUTH_SUCCESS = """
ایول! الان دیگه اطلاعاتت تکمیله✅
"""
USER_AUTH_ALREADY_EXIST = """
قبلا هویتت رو گفتی. اگه می‌خوای چیزی رو تغییر بدی بهمون مستقیما پیام بده :)
"""

USER_HAS_NO_ACCESS = """
ببخشید ولی شما دسترسی به این دستور رو ندارید!
"""

NO_PENDING_JOIN_REQUESTS = """
درخواست ورود به گروه تاییدنشده‌ای وجود نداره رئیس!
"""

CANCEL_CONVERSATION = """
کنسله.
"""

NO_ACTIVE_GROUP = """
هیچ گروه فعالی وجود نداره.
"""

WELCOME_TO_GROUP = """
راستی، درخواستت تایید شد.
به گروه خوش اومدی. لینک گروه تلگرام:
{}
"""

NO_ACCESS = """
شما دسترسی اجرای این دستور رو ندارید! شرمنده :)
"""

SEND_CHAT_ID_SUCCESS = """
برات اونور فرستادم رئیس 😘
"""

PRIORITY_EMOJIS = {
    "very_high": "🟥",
    "high": "🟧",
    "medium": "🟨",
    "low": "🟩",
}

PRIORITY_NAMES = {
    "very_high": "خیلی فوری",
    "high": "فوری",
    "medium": "معمولی",
    "low": "غیرضروری",
}

PRIORITY_LEVEL_MAP = {
    "very_high": ("خیلی فوری", "🟥"),
    "high": ("فوری", "🟧"),
    "medium": ("معمولی", "🟨"),
    "low": ("غیرضروری", "🟩"),
}

NO_GROUP = """
این دستور فقط باید در گروه‌ها و سوپرگروه‌ها اجرا بشه.
"""

GROUP_NOT_FOUND = """
گروه با شناسه‌ی این‌جا پیدا نشد!
"""

NO_PENDING_TASKS = """
هیچ تسکی در انتظار نیست!
"""

TASK_LIST_HEADER = "تسک‌های در انتظار:\n\n"

TASK_DETAILS_HEADER = """
جزئیات تسک:
عنوان: {title}
شرح: {description}
اولویت: {priority_name}
مهلت: {deadline}
"""

TASK_PICKED_UP = """
بنازم. مسئول
{title}:
{name}
👏👏👏👏👏👏👏👏
"""

TASK_ALREADY_TAKEN = """
این تسک قبلاً به کسی اختصاص داده شده است.
"""

TASK_MARKED_DONE = """
{title}
تموم شد. مبارک خیلیا.
🎉🎉🎉🎉🎉🎉
"""

ERROR_TASK_ASSIGNMENT = """
در اختصاص دادن تسک به شما مشکلی پیش آمده است.
"""

ERROR_TASK_DONE = """
این تسک را نمی‌توانید به عنوان انجام شده علامت‌گذاری کنید، چون به شما اختصاص نیافته است.
"""

INVALID_COMMAND = """
دستور نامعتبری ارسال شده است.
"""

TASK_NOT_FOUND = """
تسکی با شناسه‌ی موردنظر پیدا نشد.
"""

HELP_SUCCESS = """
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

COME_TO_PV = "بیا پیوی رئیس. اینجا که نمیشه!"

NO_ACTIVE_GROUP_MEMBER = "شما در هیچ گروه فعالی عضو نیستید."

SELECT_GROUP_HEADER = "لطفاً گروه مورد نظر را برای تعریف تسک انتخاب کنید:"

GROUP_NOT_FOUND = "گروه انتخاب‌شده یافت نشد. لطفاً دوباره تلاش کنید."

ENTER_TITLE = "عنوان تسک را وارد کنید:"

ENTER_DESCRIPTION = "توضیحات مربوط به تسک را وارد کنید:"

SELECT_URGENCY = "لطفاً فوریت تسک را انتخاب کنید:"

ENTER_DEADLINE_DAYS = "لطفاً تعداد روزهای باقی‌مانده تا ددلاین را وارد کنید (عدد صحیح):"

INVALID_DEADLINE_INPUT = "ورودی نامعتبر است. لطفاً یک عدد صحیح وارد کنید."

TASK_CREATED_SUCCESS = "✅ تسک با موفقیت ایجاد شد!"
