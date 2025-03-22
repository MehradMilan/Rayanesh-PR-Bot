from asgiref.sync import sync_to_async
import typing
from telegram import User

from user.models import TelegramUser, Group, GroupMembership


@sync_to_async
def get_or_create_telegram_user(user: User) -> typing.Tuple[TelegramUser, bool]:
    return TelegramUser.objects.get_or_create(
        telegram_id=user.id,
        defaults={"username": user.username},
    )


@sync_to_async
def get_group_by_id(group_id: str) -> Group:
    return Group.objects.filter(id=group_id).first()


@sync_to_async
def get_or_create_group_membership(
    user: User, group: Group
) -> typing.Tuple[GroupMembership, bool]:
    return GroupMembership.objects.get_or_create(user=user, group=group)


@sync_to_async
def get_telegram_user_by_id(telegram_id: str) -> TelegramUser:
    return TelegramUser.objects.filter(telegram_id=telegram_id).first()


@sync_to_async
def get_pending_group_memberships() -> typing.List[GroupMembership]:
    return list(GroupMembership.objects.filter(is_approved=False))


@sync_to_async
def get_group_membership_by_id(membership_id: str) -> GroupMembership:
    return GroupMembership.objects.get(id=membership_id)


@sync_to_async
def save_group_membership(group_membership: GroupMembership) -> None:
    group_membership.save()
    return


@sync_to_async
def save_user(user: TelegramUser) -> None:
    user.save()
    return
