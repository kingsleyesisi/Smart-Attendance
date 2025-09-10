from celery import shared_task
from django.core.mail import send_mail
from django.utils.timezone import now
from datetime import timedelta
from apps.accounts.models import ClassSession

@shared_task
def send_class_reminders():
    upcoming_classes = ClassSession.objects.filter(
        start_time__lte=now() + timedelta(minutes=10),
        start_time__gte=now()
    )

    for session in upcoming_classes:
        subject = f"Reminder: {session.title}"
        message = f"Your class '{session.title}' starts at {session.start_time.strftime('%H:%M')}."
        send_mail(
            subject,
            message,
            "noreply@Delsu.com",
            [session.student.email],
            fail_silently=False,
        )
