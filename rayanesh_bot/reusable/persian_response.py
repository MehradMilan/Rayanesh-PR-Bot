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
بات عوض شده و حال ندارم هلپ جدید بنویسم!
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

TAKEN_TASK_REMINDER_MESSAGE = """
🔔 *یادآوری تسک‌ها:*

*گروه:* {group_title}
این تسک‌ها گردن گرفته شدن ولی هنوز انجام نشدن ستونا.

{tasks}
"""

TAKEN_TASK_DETAILS = """
- *عنوان تسک:* {task_title}
- *اولویت:* {priority} {priority_emoji}
- *زمان باقی‌مانده:* {remaining_time} ساعت
- *مسئول:* @{assignee}
- /details\_{id}  /done\_{id}
-----
"""

NON_TAKEN_TASK_REMINDER_MESSAGE = """
🔔 *«گردن بگیریم»!*

*گروه:* {group_title}
این تسک‌ها رو کسی هنوز گردن نگرفته که انجام بدیم.

{tasks}
"""

NON_TAKEN_TASK_DETAILS = """
- *عنوان تسک:* {task_title}
- *اولویت:* {priority} {priority_emoji}
- /details\_{id}  /pickup\_{id}
-----
"""

GARDAN_BEGIRID = """
ملت پاشید بیاید گردن بگیرید!\n
"""

OPEN_GATE_MESSAGE_8 = """
🐓🐓🐓
قوقولی قوقو صبح شده؛ بع و بع و بع ببعیه بیدار شده.؛ واق و واق و واق هاپوئه چشش وا شده.
پنجره‌ها رو رو به حیاط باز کنید. زندگی رو دوباره آغاز کنید.
به همه بگید «صبح بخیییرررر«.

/opened_{id}  /holiday_{id}
"""

OPEN_GATE_MESSAGE_9 = """
🧠🧠🧠
جوون ایرانی پاشو. در رایانشو باز کنییییدد. کلاسا رو بریید. هوش زدید بفرستید.

/opened_{id}  /holiday_{id}
"""

OPEN_GATE_MESSAGE_10 = """
🚪🚪🚪
پاشید دیگه گشادا :// یعنی چی که در رایانش بسته‌ست؟؟

/opened_{id}  /holiday_{id}
"""

CLOSE_GATE_MESSAGE_20 = """
🏚🏚🏚
نخود نخود هر که رود خانه‌ی خود. درو کسی می‌بنده؟ 

/closed_{id}
"""

CLOSE_GATE_MESSAGE_21 = """
از نمک ریختن خسته شدم. ایده‌ای داشتید بگید اینو عوض کنیم.

/closed_{id}
"""

CLOSE_GATE_MESSAGE_22 = """
🚨🚨🚨

بیبو بیبو بیبو. درو ببندید ابلفضلی حراست درمون نذاره.

/closed_{id}
"""

OPEN_GATE_MESSAGE_DEF = """
درو باز کنید بچه‌ها.

/opened_{id}  /holiday_{id}
"""

CLOSE_GATE_MESSAGE_DEF = """
درو ببندید بچه‌ها.

/closed_{id}
"""

OPEN_GATE_MESSAGES = {
    8: OPEN_GATE_MESSAGE_8,
    9: OPEN_GATE_MESSAGE_9,
    10: OPEN_GATE_MESSAGE_10,
}

CLOSE_GATE_MESSAGES = {
    20: CLOSE_GATE_MESSAGE_20,
    21: CLOSE_GATE_MESSAGE_21,
    22: CLOSE_GATE_MESSAGE_22,
}

GATE_NOT_FOUND = """
دروازه‌ای با شناسه‌ی موردنظر پیدا نشد.
"""

OPENED_GATE_RESPONSE = """
در توسط {name} باز شد. 🎉
"""

CLOSED_GATE_RESPONSE = """
در توسط {name} بسته شد. 🕊
"""

HOLIDAY_GATE_RESPONSE = """
باشه پس. شوبز. 🌚
"""
