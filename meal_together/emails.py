from django.utils.http import urlsafe_base64_encode
from meal_together.helpers import account_activation_token
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.urls import reverse
from .tasks import send_email_task



def send_activation_link(current_site, user):
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = account_activation_token.make_token(user)
    activation_link = f"http://{current_site.domain}{reverse('activate', kwargs={'uidb64': uid, 'token': token})}"
    context = {"user": user, "activation_link": activation_link}
    subject = "Activate Your Account"
    message = render_to_string(
        "emails/account_activation_email.html",
        context,
    )

    send_email_task.delay(
        subject,
        message,
        [user.email],
    )


def send_invitation_email(current_site, invited_users, session):
    session_link = f"http://{current_site}/sessions/{session.id}"
    subject = f"You've been invited to the meal session: {session.name}"
    context = {
        "session": session,
        "session_link": session_link
    }
    message = render_to_string(
        "emails/session_invitation_email.html",
        context,
    )
    recipient_list = [
        user.email for user in invited_users if user.email and user != session.creator
    ]

    send_email_task.delay(
        subject,
        message,
        recipient_list,
    )


def send_session_update_email(current_site, changes, session):
    context = {
        "changes": changes,
        "session_name": session.name,
        "session_link": f"http://{current_site}/sessions/{session.id}/",
    }

    message = render_to_string("emails/session_update_notification.html", context)

    subject = f"Updates to the session: {session.name}"
    recipient_list = [
        participant.email
        for participant in session.participants.all()
        if participant.email and participant.email != session.creator.email
    ]

    send_email_task.delay(
        subject,
        message,
        recipient_list,
    )


def send_order_update_email(current_site, changes, order):
    context = {
        "changes": changes,
        "order_id": order.id,
        "session_name": order.session.name,
        "order_link": f"http://{current_site}/sessions/{order.session.id}/",
    }

    message = render_to_string("emails/order_update_notification.html", context)

    subject = f"Your order has been updated in the session: {order.session.name}"
    recipient_list = [order.user.email] if order.user.email else []

    send_email_task.delay(
        subject,
        message,
        recipient_list,
    )
