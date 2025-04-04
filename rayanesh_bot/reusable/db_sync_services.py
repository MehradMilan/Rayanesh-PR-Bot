from asgiref.sync import sync_to_async
import typing
from telegram import User

from user.models import TelegramUser, Group, GroupMembership, Task
from document.models import Document, DocumentGroupAccess, DocumentUserAccess
from raya.models import Gate
from music.models import Playlist


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


@sync_to_async
def get_user_in_group_membership(group_membership: GroupMembership) -> TelegramUser:
    return group_membership.user


@sync_to_async
def get_group_in_group_membership(group_membership: GroupMembership) -> Group:
    return group_membership.group


@sync_to_async
def get_all_active_groups() -> list[Group]:
    return list(Group.objects.filter(is_active=True))


@sync_to_async
def get_group_by_id(group_id: int) -> Group:
    return Group.objects.get(id=group_id)


@sync_to_async
def get_group_members(group: Group) -> list[TelegramUser]:
    return list(
        TelegramUser.objects.filter(
            groupmembership__group=group, groupmembership__is_approved=True
        ).distinct()
    )


@sync_to_async
def get_user_groups(user):
    return list(
        Group.objects.filter(
            groupmembership__user=user, groupmembership__is_approved=True
        ).distinct()
    )


@sync_to_async
def get_group_members_count(group: Group) -> int:
    return TelegramUser.objects.filter(
        groupmembership__group=group, groupmembership__is_approved=True
    ).count()


@sync_to_async
def get_or_create_document(
    google_id: str,
    link: str,
    user: TelegramUser,
    directory_id: str = None,
    is_directory: bool = False,
) -> typing.Tuple[Document, bool]:
    return Document.objects.get_or_create(
        google_id=google_id,
        defaults={
            "owner_user": user,
            "link": link,
            "directory_id": directory_id or "",
            "is_directory": is_directory,
        },
    )


@sync_to_async
def save_document(document: Document) -> None:
    document.save()
    return


@sync_to_async
def get_or_create_document_group_access(
    document: Document, group: Group, access_level: str
) -> DocumentGroupAccess:
    return DocumentGroupAccess.objects.get_or_create(
        document=document, group=group, defaults={"access_level": access_level}
    )


@sync_to_async
def get_or_create_document_user_access(
    document: Document, user: TelegramUser, access_level: str
) -> DocumentUserAccess:
    return DocumentUserAccess.objects.get_or_create(
        document=document, user=user, defaults={"access_level": access_level}
    )


@sync_to_async
def get_task_by_id(task_id: str) -> Task:
    return Task.objects.filter(id=task_id).first()


@sync_to_async
def assigne_user_to_task(user: TelegramUser, task: Task) -> None:
    task.state = task.TAKEN_STATE
    task.assignee_user = user
    task.save()
    return


@sync_to_async
def get_task_assignee(task: Task) -> TelegramUser | None:
    return task.assignee_user


@sync_to_async
def mark_task_as_done(task: Task) -> None:
    task.state = Task.DONE_STATE
    task.save()
    return


@sync_to_async
def get_document_from_document_user_access(dua: DocumentUserAccess) -> Document:
    return dua.document


@sync_to_async
def get_document_from_document_group_access(dga: DocumentGroupAccess) -> Document:
    return dga.document


@sync_to_async
def close_gate(gate: Gate) -> None:
    gate.is_open = False
    gate.save()
    return


@sync_to_async
def open_gate(gate: Gate) -> None:
    gate.is_open = True
    gate.save()
    return


@sync_to_async
def deactivate_gate(gate: Gate) -> None:
    gate.is_active = False
    gate.save()
    return


@sync_to_async
def activate_gate(gate: Gate) -> None:
    gate.is_active = True
    gate.save()
    return


@sync_to_async
def get_playlist_owner(playlist: Playlist) -> TelegramUser:
    return playlist.owner
