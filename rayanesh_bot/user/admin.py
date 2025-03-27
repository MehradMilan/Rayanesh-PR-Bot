from django.contrib import admin
from .models import TelegramUser, Group, GroupMembership


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


admin.site.register(TelegramUser, TelegramUserAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(GroupMembership, GroupMembershipAdmin)
