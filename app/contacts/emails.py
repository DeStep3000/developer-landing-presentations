from django.conf import settings
from django.core.mail import EmailMultiAlternatives

from contacts.models import ContactRequest


class ContactNotificationError(Exception):
    """Raised when owner or user notification cannot be sent."""


def send_contact_notifications(contact: ContactRequest) -> tuple[bool, bool]:
    try:
        owner_sent = send_owner_notification(contact)
        user_sent = send_user_copy(contact)
    except Exception as exc:  # noqa: BLE001 - converted to service-level API error.
        raise ContactNotificationError(str(exc)) from exc

    return owner_sent > 0, user_sent > 0


def send_owner_notification(contact: ContactRequest) -> int:
    subject = f"New landing contact: {contact.name}"
    text_body = (
        f"Name: {contact.name}\n"
        f"Phone: {contact.phone}\n"
        f"Email: {contact.email}\n"
        f"Type: {contact.request_type}\n"
        f"Sentiment: {contact.sentiment}\n"
        f"AI provider: {contact.ai_provider}\n\n"
        f"Comment:\n{contact.comment}\n\n"
        f"Suggested reply:\n{contact.ai_reply}"
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[settings.SITE_OWNER_EMAIL],
        reply_to=[contact.email],
    )
    return message.send(fail_silently=False)


def send_user_copy(contact: ContactRequest) -> int:
    subject = "Ваше сообщение получено"
    text_body = (
        f"{contact.name}, здравствуйте!\n\n"
        f"{contact.ai_reply}\n\n"
        "Копия вашего сообщения:\n"
        f"{contact.comment}"
    )
    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[contact.email],
    )
    return message.send(fail_silently=False)
