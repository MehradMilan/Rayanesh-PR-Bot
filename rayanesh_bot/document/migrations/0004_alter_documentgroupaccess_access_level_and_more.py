# Generated by Django 5.1.7 on 2025-03-27 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("document", "0003_rename_folder_id_document_directory_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documentgroupaccess",
            name="access_level",
            field=models.CharField(
                choices=[
                    ("writer", "writer"),
                    ("commenter", "commenter"),
                    ("reader", "reader"),
                ],
                default="reader",
                max_length=10,
            ),
        ),
        migrations.AlterField(
            model_name="documentuseraccess",
            name="access_level",
            field=models.CharField(
                choices=[
                    ("writer", "writer"),
                    ("commenter", "commenter"),
                    ("reader", "reader"),
                ],
                default="reader",
                max_length=10,
            ),
        ),
    ]
