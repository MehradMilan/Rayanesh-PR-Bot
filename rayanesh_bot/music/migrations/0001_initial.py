# Generated by Django 5.1.7 on 2025-03-30 16:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("user", "0008_group_task_reminder_active_alter_task_scope_group"),
    ]

    operations = [
        migrations.CreateModel(
            name="Playlist",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("is_active", models.BooleanField(default=True)),
                ("is_public", models.BooleanField(default=False)),
                ("is_accessible", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "cover_message_id",
                    models.CharField(blank=True, max_length=63, null=True),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user.telegramuser",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="SentSong",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("chat_id", models.CharField(max_length=63)),
                ("pv_message_id", models.CharField(max_length=63)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "playlist",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="music.playlist",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user.telegramuser",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Song",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=255)),
                ("channel_message_id", models.CharField(max_length=63)),
                ("caption", models.TextField(blank=True)),
                ("forwarded_at", models.DateTimeField(auto_now_add=True)),
                (
                    "added_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="user.telegramuser",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="playlist",
            name="songs",
            field=models.ManyToManyField(
                blank=True, related_name="playlists", to="music.song"
            ),
        ),
    ]
