import typing
from datetime import timedelta
import math
import random

import celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger
from core.celery import REMIND_TASKS_IN_GROUPS_QUEUE, app as celery_app
from django.db.models import F, ExpressionWrapper, DurationField, Q
from django.utils import timezone

import reusable.db_sync_services as db_sync_services
import reusable.persian_response as persian
from user.models import TelegramUser, Group, Task, GroupMembership
import reusable.telegram_bots

logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender: celery.Celery, **_) -> None:
    sender.add_periodic_task(
        crontab(minute=0, hour=8),
        remind_taken_tasks_in_groups.s(),
        name="remind_taken_tasks_in_groups",
        queue=REMIND_TASKS_IN_GROUPS_QUEUE,
    )
    sender.add_periodic_task(
        crontab(minute=30, hour=23),
        remind_nontaken_tasks_in_groups.s(),
        name="remind_nontaken_tasks_in_groups",
        queue=REMIND_TASKS_IN_GROUPS_QUEUE,
    )


async def extract_deeplink_from_message(
    message_text: str,
) -> typing.Tuple[str, typing.List[str]]:
    input = message_text.split(" ")
    input.pop(0)
    if input:
        params = input.pop(0).split("-")
        return (params[0], params[1:])
    return (None, [])


async def join_group_request(telegram_user_id, group_id):
    group = await db_sync_services.get_group_by_id(group_id)
    if group is None:
        return persian.GROUP_NOT_FOUND
    user: TelegramUser = await db_sync_services.get_telegram_user_by_id(
        telegram_user_id
    )
    if user is None or not user.is_authorized:
        return persian.USER_UNAUTHORIZED
    else:
        group_membership, created = (
            await db_sync_services.get_or_create_group_membership(
                user=user, group=group
            )
        )
        if created:
            return persian.GROUP_REQUEST_SUCCESS
        else:
            return persian.GROUP_REQUEST_ALREADY_EXIST


@celery.shared_task(
    name="remind_taken_tasks_in_groups", queue=REMIND_TASKS_IN_GROUPS_QUEUE
)
def remind_taken_tasks_in_groups():
    groups = Group.objects.filter(task_reminder_active=True).exclude(
        Q(chat_id__isnull=True) | Q(chat_id__exact="")
    )
    telegram_bot = reusable.telegram_bots.get_telegram_bot()
    for group in groups:
        message = persian.TAKEN_TASK_REMINDER_MESSAGE.format(
            group_title=group.title, tasks=""
        )
        tasks = list(
            group.tasks.annotate(
                remaining_time=ExpressionWrapper(
                    F("deadline") - timezone.now(), output_field=DurationField()
                )
            ).filter(
                state=Task.TAKEN_STATE,
                deadline__gte=timezone.now(),
                deadline__lte=timezone.now() + timedelta(hours=24),
            )
        )
        if not tasks:
            logger.info(f"Group {group} has no taken pending tasks.")
            continue
        for task in tasks:
            remaining_hours = task.remaining_time.total_seconds() // 3600
            assignee = task.assignee_user

            priority, priority_emoji = persian.PRIORITY_LEVEL_MAP.get(
                task.priority_level, ("نامشخص", "🟩")
            )
            assignee_username = assignee.username if assignee else "نامشخص"

            task_details = persian.TAKEN_TASK_DETAILS.format(
                task_title=task.title,
                priority=priority,
                priority_emoji=priority_emoji,
                remaining_time=remaining_hours,
                assignee=assignee_username,
                id=task.id,
            )
            message += task_details

        reusable.telegram_bots.send_message_sync(
            bot=telegram_bot, chat_id=group.chat_id, message=message
        )


@celery.shared_task(
    name="remind_nontaken_tasks_in_groups", queue=REMIND_TASKS_IN_GROUPS_QUEUE
)
def remind_nontaken_tasks_in_groups():
    groups = Group.objects.filter(task_reminder_active=True).exclude(
        Q(chat_id__isnull=True) | Q(chat_id__exact="")
    )
    telegram_bot = reusable.telegram_bots.get_telegram_bot()
    for group in groups:
        message = persian.NON_TAKEN_TASK_REMINDER_MESSAGE.format(
            group_title=group.title, tasks=""
        )
        tasks = group.tasks.filter(
            state=Task.INITIAL_STATE, deadline__gte=timezone.now()
        )
        if not tasks:
            logger.info(f"Group {group} has no non-taken pending tasks.")
            continue
        for task in tasks:
            priority, priority_emoji = persian.PRIORITY_LEVEL_MAP.get(
                task.priority_level, ("نامشخص", "🟩")
            )
            task_details = persian.NON_TAKEN_TASK_DETAILS.format(
                task_title=task.title,
                priority=priority,
                priority_emoji=priority_emoji,
                id=task.id,
            )
            message += task_details

        # task_assignments = (
        #     Task.objects.filter(
        #         scope_group=group, state__in=[Task.TAKEN_STATE, Task.DONE_STATE]
        #     )
        #     .values("assignee_user")
        #     .annotate(task_count=Count("assignee_user"))
        #     .order_by("task_count")
        # )

        # memberships = (
        #     GroupMembership.objects.filter(group=group)
        #     .exclude(Q(user__username__isnull=True) | Q(user__username__exact=""))
        #     .values_list("user__username", flat=True)
        # )
        # user_task_counts = {
        #     assignment["assignee_user"]: assignment["task_count"]
        #     for assignment in task_assignments
        # }
        # eligible_users = []
        # for user in memberships:
        #     task_count = user_task_counts.get(user.id, 0)
        #     weight = calculate_weight(task_count)
        #     eligible_users.append((user, weight))

        # selected_users: typing.List[TelegramUser] = random.choices(
        #     population=[user for user, weight in eligible_users],
        #     weights=[weight for user, weight in eligible_users],
        #     k=5,
        # )
        # for user in selected_users:
        #     message += f"@{user.username} \n"
        memberships = (
            GroupMembership.objects.filter(group=group, is_approved=True)
            .exclude(Q(user__username__isnull=True) | Q(user__username__exact=""))
            .values_list("user__username", flat=True)
            .distinct()
            .order_by("?")[:5]
        )
        if memberships:
            message += persian.GARDAN_BEGIRID
            for username in memberships:
                message += f"@{username} ".replace("_", "\_")

        reusable.telegram_bots.send_message_sync(
            bot=telegram_bot, chat_id=group.chat_id, message=message
        )


def calculate_weight(task_count, base=2, max_weight=10):
    if task_count == 0:
        return max_weight
    weight = max_weight / (1 + math.log(task_count + 1, base))
    return weight
