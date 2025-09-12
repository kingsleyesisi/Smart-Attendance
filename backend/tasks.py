from celery import shared_task
from django.utils.timezone import now, timedelta
from django.core.mail import send_mail
from apps.accounts.models import ClassSession


@shared_task
def send_class_reminders():
    current_time = now()
    reminder_window = current_time + timedelta(minutes=10)
    sessions = ClassSession.objects.filter(
        start_time__gte=current_time,
        start_time__lte=reminder_window,
        reminder_sent=False,
    )

    for session in sessions:
        for student in session.students.all():
            send_mail(
                subject=f"Reminder: {session.title} starts soon",
                message=(
                    f"Dear {student.first_name},\n\n"
                    f"Your class '{session.title}' starts at {session.start_time.strftime('%H:%M')}. "
                    "This is a friendly reminder."
                ),
                from_email="princendubuisidev@gmail.com",
                recipient_list=[student.email],
                fail_silently=False,
            )
            print(f"Sent reminder to: {student.email}")
        #to avoid repetition
        session.reminder_sent = True
        session.save()

