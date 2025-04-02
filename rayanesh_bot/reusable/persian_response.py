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

/opened\_{id}  /holiday\_{id}
"""

OPEN_GATE_MESSAGE_9 = """
🧠🧠🧠
جوون ایرانی پاشو. در رایانشو باز کنییییدد. کلاسا رو بریید. هوش زدید بفرستید.

/opened\_{id}  /holiday\_{id}
"""

OPEN_GATE_MESSAGE_10 = """
🚪🚪🚪
پاشید دیگه گشادا :// یعنی چی که در رایانش بسته‌ست؟؟

/opened\_{id}  /holiday\_{id}
"""

CLOSE_GATE_MESSAGE_20 = """
🏚🏚🏚
نخود نخود هر که رود خانه‌ی خود. درو کسی می‌بنده؟ 

/closed\_{id}
"""

CLOSE_GATE_MESSAGE_21 = """
از نمک ریختن خسته شدم. ایده‌ای داشتید بگید اینو عوض کنیم.

/closed\_{id}
"""

CLOSE_GATE_MESSAGE_22 = """
🚨🚨🚨

بیبو بیبو بیبو. درو ببندید ابلفضلی حراست درمون نذاره.

/closed\_{id}
"""

OPEN_GATE_MESSAGE_DEF = """
درو باز کنید بچه‌ها.

/opened\_{id}  /holiday\_{id}
"""

CLOSE_GATE_MESSAGE_DEF = """
درو ببندید بچه‌ها.

/closed\_{id}
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

PLAYLIST_COVER_CAPTION = """
🎶 Playlist: {name}
👤 Owner: @{username}

🎵 Songs count: {count}
📅 Playlist on the air from: {created_at}
---
{description}

"""

USE_IN_PRIVATE_CHAT = """
⚠️ Please use this command in a private chat.
"""

PLAYLIST_NOT_FOUND = """
⚠️ Playlist not found or not owned by you.
"""

SEND_PLAYLIST_TITLE = """
📝 Send the new title for your playlist:
"""

PLAYLIST_TITLE_UPDATE_SUCCESS = """
✅ Playlist title updated to: *{new_title}*
"""

PLAYLIST_SEND_NEW_COVER = """
🖼️ Send a new photo to use as the cover:
"""

PLAYLIST_SEND_COVER_INVALID_PHOTO = """
❗Please send a valid photo.
"""

PLAYLIST_COVER_UPDATE_SUCCESS = """
✅ Playlist cover updated successfully.
"""

EMPTY_PLAYLIST = """
There are no songs in this playlist.
"""

SONGS_LIST_PLAYLIST = """
🎶 Song List for Playlist {name}:\n{song_list}
"""

SONG_NOT_FOUND = """
⚠️ Song not found.
"""

INVALID_ACCESS_TO_PLAYLIST = """
❌ You don't have permission to modify this playlist.
"""

SONG_REMOVE_SUCCESS = """
✅ Song {name} has been removed.
"""

CHOOSE_PLAYLIST_ADD_MUSIC = """
Choose a playlist to add your music to:
"""

BATCH_SEND_MUSIC_EXPL = """
You can now send multiple music files. Type /done_batch_forward when done.
"""

INVALID_AUDIO_FILE = """
❗ Please send a valid music file.
"""

PLAYLIST_NOT_SELECTED = """
❗ No Playlist is selected!
"""

MUSIC_CAPTION = """
🎵 {song_name}\n💫 Added by {username}\n\n◾ @{rayanesh_id}
"""  # In English

BATCH_SEND_MUSIC_FAIL = """
❌ {failed_count} song(s) failed to add. Try sending those individually.
"""

BATCH_SEND_MUSIC_SUCCESS = """
✅ All songs were successfully added to the playlist!
"""

NO_PLAYLIST_EXIST = """
There are no public playlists available.
"""

SEND_MUSIC_AUDIO_FILE = """
Send me the music file now as audio.
"""

ASK_SONG_NAME = """
What name should I give this track?
"""

YES = """
✅ Yes
"""

NO = """
❌ No
"""

SEND_MUSIC_SUCCESS_ASK_SEND_RAYA_MUSIC = """
✅ Your music has been added to the playlist!
🥷 Original message was deleted for better Experience.

Do you want to send this track to رایاموزیک?
"""

SEND_TO_RAYA_MUSIC_SUCCESS = """
🎶 Track sent to رایاموزیک!
"""

SEND_TO_RAYA_MUSIC_FAIL = """
⚠️ Failed to send to رایاموزیک.
"""

NOT_SEND_TO_RAYA_MUSIC = """
👍 Got it, not sending to رایاموزیک.
"""

PLAYLIST_TYPE_EMOJI_MAP = {
    "owner": "🧺",
    "shared": "🤝",
    "public": "🌍",
}  # No change in keys

PLAYLIST_DEFAULT_TYPE_EMOJI = "📁"

PLAYLIST_TYPES_EXPL = """
📂 *Your Playlists*

🧺 Your own playlists
🤝 Shared with you
🌍 Publicly accessible
"""

SELECT_PLAYLIST_TO_LISTEN = """
🎼 Select a playlist to listen:
"""

ASK_DELETE_PREVIOUS_SONGS = """
Do you want to delete previously sent tracks?
"""

LISTEN_MUSIC_SUCCESS = """
🎶 Your playlist is ready to enjoy!
"""

PLAYLIST_NAME = """
📝 Please enter a name for your playlist:
"""

PLAYLIST_DESCRIPTION = """
💬 Enter a description (or send - to skip):
"""

PLAYLIST_DESCRIPTION_MAX_LENGTH = """
⚠️ The description must be under {count} characters.\nPlease try again:
"""

PLAYLIST_SEND_COVER = """
🖼️ Now, send a photo to use as the cover image:
"""

PLAYLIST_CREATE_SUCCESS = """
✅ Playlist «{name}» created successfully!
"""

SELECT_PLAYLIST_TO_SEE_DETAILS = """
👇 Select a playlist to see its details:
"""

CHANGE_VISIBILITY_COMMAND = """
👀 Change visibility: /{to_state}_{playlist_id}

"""

PLAYLIST_DETAIL_CAPTION = """
📝 Edit title: /edit_title_{playlist_id}
🖼️ Edit cover: /edit_cover_{playlist_id}
🎶 View all songs: /all_songs_{playlist_id}

📨 Share playlist, 🎧 Listen together: {share_playlist_uri}
"""

PRIVATE_SUCCESS = """
now private 🔒
"""

PUBLIC_SUCCESS = """
now public ✅
"""

CHANGE_VISIBILITY_SUCCESS = """
Playlist *{name}* is {status}
"""
