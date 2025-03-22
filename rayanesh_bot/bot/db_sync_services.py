from asgiref.sync import sync_to_async
import typing
from telegram import User

from user.models import TelegramUser


@sync_to_async
def get_or_create_telegram_user(user: User) -> typing.Tuple[TelegramUser, bool]:
    return TelegramUser.objects.get_or_create(
        telegram_id=user.id,
        defaults={"username": user.username},
    )


@sync_to_async
def get_telegram_user_by_id(telegram_id: str) -> TelegramUser:
    return TelegramUser.objects.filter(telegram_id=telegram_id).first()


@sync_to_async
def save_user(user: TelegramUser) -> None:
    user.save()
