from django.contrib import admin
from .models import Song, Playlist, SentSong
from user.models import TelegramUser


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ("name", "channel_message_id", "added_by", "forwarded_at")
    search_fields = ("name", "channel_message_id", "added_by__user_id")
    list_filter = ("forwarded_at",)
    autocomplete_fields = ("added_by",)
    readonly_fields = ("forwarded_at",)
    fields = (
        "name",
        "channel_message_id",
        "added_by",
        "caption",
        "forwarded_at",
    )
    ordering = ("-forwarded_at",)


class SongInline(admin.TabularInline):
    model = Playlist.songs.through
    extra = 0
    verbose_name = "Song in Playlist"
    verbose_name_plural = "Songs in Playlist"
    autocomplete_fields = ("song",)


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "is_active",
        "is_public",
        "is_accessible",
        "created_at",
    )
    search_fields = ("name", "description", "owner__user_id")
    list_filter = ("is_active", "is_public", "is_accessible")
    autocomplete_fields = ("owner",)
    readonly_fields = ("created_at",)
    inlines = [SongInline]
    fields = (
        "name",
        "owner",
        "is_active",
        "is_public",
        "is_accessible",
        "description",
        "cover_message_id",
        "created_at",
    )
    ordering = ("-created_at",)


@admin.register(SentSong)
class SentSongAdmin(admin.ModelAdmin):
    list_display = ("user", "chat_id", "pv_message_id", "playlist", "created_at")
    search_fields = ("chat_id", "pv_message_id", "playlist__name", "user__user_id")
    list_filter = ("created_at",)
    autocomplete_fields = ("user", "playlist")
    readonly_fields = ("created_at",)
    fields = (
        "user",
        "chat_id",
        "pv_message_id",
        "playlist",
        "created_at",
    )
    ordering = ("-created_at",)
