from django.contrib import admin
from .models import TelegramUser, Group, GroupMembership, Task


class TelegramUserAdmin(admin.ModelAdmin):
    list_display = (
        "username",
        "email",
        "name",
        "telegram_id",
        "is_authorized",
        "created_at",
    )
    search_fields = ("username", "email")
    list_filter = ("is_authorized", "user_type")
    ordering = ("created_at",)


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "is_active",
        "created_at",
        "telegram_chat_link",
    )
    search_fields = ("title",)
    list_filter = ("is_active",)
    ordering = ("created_at",)


class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "group", "is_approved", "requested_at", "joined_at")
    search_fields = ("user__username", "group__title")
    list_filter = ("is_approved", "group")
    ordering = ("requested_at",)


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "scope_group",
        "priority_level",
        "state",
        "owner_user",
        "assignee_user",
        "created_at",
        "assigned_at",
        "done_at",
    )

    list_filter = (
        "priority_level",
        "state",
        "scope_group",
        "created_at",
        "done_at",
    )

    search_fields = (
        "title",
        "description",
        "owner_user__username",
        "assignee_user__username",
        "scope_group__title",
    )

    list_editable = ("state",)

    autocomplete_fields = ("owner_user", "assignee_user", "scope_group")

    readonly_fields = ("created_at", "assigned_at", "done_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "title",
                    "description",
                    "scope_group",
                    "priority_level",
                    "deadline",
                )
            },
        ),
        (
            "Assignment Info",
            {
                "fields": (
                    "owner_user",
                    "assignee_user",
                    "state",
                    "created_at",
                    "assigned_at",
                    "done_at",
                )
            },
        ),
    )


admin.site.register(TelegramUser, TelegramUserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(GroupMembership, GroupMembershipAdmin)
