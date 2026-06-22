from django.db import models


class ContactRequest(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        NOTIFICATION_FAILED = "notification_failed", "Notification failed"

    class Sentiment(models.TextChoices):
        POSITIVE = "positive", "Positive"
        NEUTRAL = "neutral", "Neutral"
        NEGATIVE = "negative", "Negative"

    class RequestType(models.TextChoices):
        JOB_OFFER = "job_offer", "Job offer"
        CONSULTATION = "consultation", "Consultation"
        FEEDBACK = "feedback", "Feedback"
        QUESTION = "question", "Question"
        OTHER = "other", "Other"

    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=32)
    email = models.EmailField()
    comment = models.TextField(max_length=2000)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.RECEIVED)
    sentiment = models.CharField(
        max_length=16,
        choices=Sentiment.choices,
        default=Sentiment.NEUTRAL,
    )
    request_type = models.CharField(
        max_length=32,
        choices=RequestType.choices,
        default=RequestType.OTHER,
    )
    ai_reply = models.TextField(blank=True)
    ai_provider = models.CharField(max_length=80, blank=True)
    ai_fallback_reason = models.CharField(max_length=255, blank=True)
    owner_email_sent = models.BooleanField(default=False)
    user_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "-created_at"], name="contact_status_created_idx"),
            models.Index(fields=["request_type", "-created_at"], name="contact_type_created_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.name} <{self.email}> ({self.request_type})"
