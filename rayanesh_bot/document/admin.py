from django.contrib import admin
from .models import Document, DocumentUserAccess, DocumentGroupAccess


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "google_id",
        "owner_user",
        "is_directory",
        "is_finalized",
        "created_at",
    )
    list_filter = ("is_directory", "is_finalized", "created_at")
    search_fields = ("google_id", "owner_user__name", "link", "directory_id")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(DocumentUserAccess)
class DocumentUserAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "document", "access_level", "access_count", "updated_at")
    list_filter = ("access_level", "updated_at")
    search_fields = ("user__name", "user__email", "document__google_id")
    readonly_fields = ("updated_at",)
    ordering = ("-updated_at",)


@admin.register(DocumentGroupAccess)
class DocumentGroupAccessAdmin(admin.ModelAdmin):
    list_display = ("group", "document", "access_level", "is_active", "updated_at")
    list_filter = ("access_level", "is_active", "updated_at")
    search_fields = ("group__title", "document__google_id")
    readonly_fields = ("updated_at",)
    ordering = ("-updated_at",)
