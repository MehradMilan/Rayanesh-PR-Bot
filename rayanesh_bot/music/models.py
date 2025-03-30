from django.db import models
from user.models import TelegramUser


class Song(models.Model):
    name = models.CharField(max_length=255, blank=True)
    channel_message_id = models.CharField(max_length=63)
    added_by = models.ForeignKey(TelegramUser, on_delete=models.SET_NULL, null=True)
    caption = models.TextField(blank=True)
    forwarded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Song {self.id}"


class Playlist(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    is_accessible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=True, blank=True)
    cover_message_id = models.CharField(max_length=63, null=True, blank=True)

    songs = models.ManyToManyField(Song, related_name="playlists", blank=True)

    def __str__(self):
        return self.name


class SentSong(models.Model):
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    chat_id = models.CharField(max_length=63)
    pv_message_id = models.CharField(max_length=63)
    playlist = models.ForeignKey(
        Playlist, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
