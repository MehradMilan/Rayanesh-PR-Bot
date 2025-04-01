import os
import argparse
import time
from telegram import Bot

import django

import reusable.telegram_bots
from user.models import TelegramUser


os.environ["DJANGO_SETTINGS_MODULE"] = "bitpin.settings"
django.setup()


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-text", type=str, required=True, help="Provide the notification text path"
    )
    args = parser.parse_args()
    return args


def send_notifications(message: str, bot: Bot):
    users = TelegramUser.objects.filter(
        is_authorized=True, user_type=TelegramUser.MANAGER_USER
    ).values_list("telegram_id", flat=True)

    total = users.count()
    success = 0
    failed = 0

    for i, user_id in enumerate(users, start=1):
        try:
            reusable.telegram_bots.send_message_sync(
                bot=bot, chat_id=user_id, message=message
            )
            success += 1
            print(f"[{i}/{total}] ✅ Sent to {user_id}")
        except Exception as e:
            print(f"[{i}/{total}] ❌ Failed to send to {user_id}: {e}")
            failed += 1

        time.sleep(0.15)

    print(f"\nDone. ✅ Success: {success} | ❌ Failed: {failed}")


def main():
    args = get_args()
    try:
        with open(args.text, "r", encoding="utf-8") as f:
            message = f.read().strip()
    except FileNotFoundError:
        print(f"❗ File not found: {args.text}")
        return
    except Exception as e:
        print(f"❗ Error reading the file: {e}")
        return

    if not message:
        print("❗ The message file is empty.")
        return
    bot = reusable.telegram_bots.get_telegram_bot()

    try:
        send_notifications(message=message, bot=bot)
    except Exception as e:
        print(f"❗ Error sending notifications: {e}")


if __name__ == "__main__":
    main()
