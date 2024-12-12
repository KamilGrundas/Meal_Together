from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now
from .models.sessions import MealSession
from background_task import background
from django.template.loader import render_to_string


@shared_task
def send_email_task(subject,message,recipient_list):

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list
    )


@background(schedule=60)
def send_deadline_notifications():
    current_time = now()
    sessions = MealSession.objects.filter(order_deadline__lte=current_time, email_sent=False)

    for session in sessions:
        subject = f"Deadline Passed for Session: {session.name}"
        message = render_to_string("emails/session_deadline_notification.html", {'session':session})
        send_email_task.delay(
            subject,
            message,
            [session.creator.email],
        )
        session.email_sent = True
        session.save()