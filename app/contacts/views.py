from django.db.models import Count, Max
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from contacts.emails import ContactNotificationError
from contacts.models import ContactRequest
from contacts.serializers import (
    ContactCreateSerializer,
    ContactReadSerializer,
    HealthSerializer,
    MetricsSerializer,
)
from contacts.services import create_contact_request
from contacts.throttling import ContactCreateRateThrottle

CONTACT_TAG = "Contact form"
OPERATIONS_TAG = "Operations"


class ContactAPIView(APIView):
    throttle_classes = [ContactCreateRateThrottle]

    @extend_schema(
        tags=[CONTACT_TAG],
        summary="Отправить заявку с лендинга",
        description=(
            "Принимает данные формы обратной связи, валидирует имя, телефон, email и "
            "комментарий, запускает AI-анализ тональности и типа запроса, сохраняет "
            "обращение, отправляет письмо владельцу сайта и копию пользователю. Если "
            "OpenAI недоступен или ключ не настроен, используется deterministic fallback, "
            "поэтому API продолжает работать."
        ),
        request=ContactCreateSerializer,
        examples=[
            OpenApiExample(
                "Consultation request",
                value={
                    "name": "Ada Lovelace",
                    "phone": "+7 999 123-45-67",
                    "email": "ada@example.com",
                    "comment": "Здравствуйте! Хочу обсудить разработку backend API для проекта.",
                },
                request_only=True,
            )
        ],
        responses={
            201: ContactReadSerializer,
            400: OpenApiResponse(description="Некорректные входные данные формы."),
            429: OpenApiResponse(description="Превышен rate limit отправки формы."),
            502: OpenApiResponse(
                description="Заявка сохранена, но email-уведомление не отправлено."
            ),
        },
    )
    def post(self, request):
        serializer = ContactCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            contact = create_contact_request(serializer.validated_data)
        except ContactNotificationError:
            return Response(
                {"detail": "Contact was saved, but email notification failed."},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(ContactReadSerializer(contact).data, status=status.HTTP_201_CREATED)


class HealthAPIView(APIView):
    @extend_schema(
        tags=[OPERATIONS_TAG],
        summary="Проверить состояние API",
        description="Возвращает простой health-check для мониторинга и деплоя.",
        responses={200: HealthSerializer},
    )
    def get(self, _request):
        return Response({"status": "ok", "service": "developer-landing-contact-api"})


class MetricsAPIView(APIView):
    @extend_schema(
        tags=[OPERATIONS_TAG],
        summary="Получить статистику обращений",
        description=(
            "Возвращает агрегированную статистику по обращениям: общее количество, "
            "количество успешных и проблемных email-уведомлений, распределение по "
            "тональности, типу запроса и дату последнего обращения."
        ),
        responses={200: MetricsSerializer},
    )
    def get(self, _request):
        contacts = ContactRequest.objects.all()
        by_sentiment = dict(contacts.values_list("sentiment").annotate(total=Count("id")))
        by_request_type = dict(contacts.values_list("request_type").annotate(total=Count("id")))
        latest = contacts.aggregate(last_contact_at=Max("created_at"))["last_contact_at"]

        return Response(
            {
                "total_contacts": contacts.count(),
                "received_contacts": contacts.filter(status=ContactRequest.Status.RECEIVED).count(),
                "notification_failed_contacts": contacts.filter(
                    status=ContactRequest.Status.NOTIFICATION_FAILED
                ).count(),
                "by_sentiment": by_sentiment,
                "by_request_type": by_request_type,
                "last_contact_at": latest,
            }
        )
