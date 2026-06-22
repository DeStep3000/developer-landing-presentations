import logging

from django.db import transaction

from contacts.ai import analyze_contact_message
from contacts.emails import ContactNotificationError, send_contact_notifications
from contacts.models import ContactRequest

logger = logging.getLogger(__name__)


def create_contact_request(validated_data: dict) -> ContactRequest:
    analysis = analyze_contact_message(
        name=validated_data["name"],
        email=validated_data["email"],
        comment=validated_data["comment"],
    )

    with transaction.atomic():
        contact = ContactRequest.objects.create(
            **validated_data,
            sentiment=analysis.sentiment,
            request_type=analysis.request_type,
            ai_reply=analysis.auto_reply,
            ai_provider=analysis.provider,
            ai_fallback_reason=analysis.fallback_reason,
        )

        try:
            owner_sent, user_sent = send_contact_notifications(contact)
        except ContactNotificationError:
            contact.status = ContactRequest.Status.NOTIFICATION_FAILED
            contact.save(update_fields=["status", "updated_at"])
            logger.exception("contact notification failed", extra={"contact_id": contact.id})
            raise

        contact.owner_email_sent = owner_sent
        contact.user_email_sent = user_sent
        contact.save(update_fields=["owner_email_sent", "user_email_sent", "updated_at"])

    logger.info(
        "contact request processed",
        extra={
            "contact_id": contact.id,
            "request_type": contact.request_type,
            "sentiment": contact.sentiment,
            "ai_provider": contact.ai_provider,
        },
    )
    return contact
