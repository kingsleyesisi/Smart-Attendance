from celery import shared_task
from django.core.mail import send_mail
from .models import User

@shared_task
def send_approval_request(user_id):
    # Send email to admin
    user = User.objects.get(id=user_id)
    send_mail(
        'Coordinator Approval Needed',
        f'New coordinator registration from {user.email}',
        'kingsleyesisi1@gmail.com',
        ['kingsleyesisi1@gmail.com'],
        fail_silently=False,
    )

@shared_task
def send_approval_notification(user_email):
    # Send approval confirmation
    send_mail(
        'Registration Approved',
        'Your coordinator account has been approved',
        'kingsleyesisi1@gmail.com',
        [user_email],
        fail_silently=False,
    )