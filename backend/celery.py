from celery import Celery
from celery.schedules import crontab
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

app = Celery("backend")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# run every minute
app.conf.beat_schedule = {
    "send-class-reminders-every-minute": {
        "task": "backend.tasks.send_class_reminders",
        "schedule": 30.0,  # check every 30 secs
    },
}
