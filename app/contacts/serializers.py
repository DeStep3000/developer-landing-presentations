from rest_framework import serializers

from contacts.models import ContactRequest


class ContactCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactRequest
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "comment",
            "status",
            "sentiment",
            "request_type",
            "ai_reply",
            "ai_provider",
            "ai_fallback_reason",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "sentiment",
            "request_type",
            "ai_reply",
            "ai_provider",
            "ai_fallback_reason",
            "created_at",
        ]

    def validate_name(self, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Name must contain at least 2 characters.")
        return value

    def validate_phone(self, value: str) -> str:
        value = value.strip()
        allowed = set("+0123456789 ()-.")
        digits = [char for char in value if char.isdigit()]

        if len(digits) < 7 or any(char not in allowed for char in value):
            raise serializers.ValidationError(
                "Phone must contain at least 7 digits and may include +, spaces, (), - or dots."
            )
        return value

    def validate_comment(self, value: str) -> str:
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError("Comment must contain at least 10 characters.")
        return value


class ContactReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactRequest
        fields = [
            "id",
            "name",
            "phone",
            "email",
            "comment",
            "status",
            "sentiment",
            "request_type",
            "ai_reply",
            "ai_provider",
            "ai_fallback_reason",
            "owner_email_sent",
            "user_email_sent",
            "created_at",
            "updated_at",
        ]


class HealthSerializer(serializers.Serializer):
    status = serializers.CharField()
    service = serializers.CharField()


class MetricsSerializer(serializers.Serializer):
    total_contacts = serializers.IntegerField()
    received_contacts = serializers.IntegerField()
    notification_failed_contacts = serializers.IntegerField()
    by_sentiment = serializers.DictField(child=serializers.IntegerField())
    by_request_type = serializers.DictField(child=serializers.IntegerField())
    last_contact_at = serializers.DateTimeField(allow_null=True)
