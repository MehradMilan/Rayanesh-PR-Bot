import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


DB_POSTGRES_BACKUP_QUEUE = "db_postgres_backup"
REMIND_TASKS_IN_GROUPS_QUEUE = "remind_tasks_in_groups"
GATEKEEPERS_QUEUE = "gatekeepers"
