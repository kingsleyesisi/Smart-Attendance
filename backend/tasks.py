from celery import shared_task
from django.utils.timezone import now, timedelta
from django.core.mail import send_mail
from apps.accounts.models import ClassSession


@shared_task
def send_class_reminders():
    sessions = ClassSession.objects.filter(
        start_time__gte=now(), start_time__lte=now() + timedelta(minutes=10)
    )

    for session in sessions:
        for student in session.students.all():
            send_mail(
                subject=f"Reminder: {session.title} starts soon",
                message=f"Dear {student.first_name or 'Student'},\n\nYour class '{session.title}' starts at {session.start_time.strftime('%H:%M')}. This is a friendly remainder.",
                from_email="princendubuisidev@gmail.com",
                recipient_list=[student.email],
                fail_silently=False,
            )
            print(f"Sent reminder to: {student.email}")
