from django.urls import path, re_path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from contacts.views import ContactAPIView, HealthAPIView, MetricsAPIView

urlpatterns = [
    path("api/contact", ContactAPIView.as_view(), name="contact-create"),
    path("api/health", HealthAPIView.as_view(), name="health"),
    path("api/metrics", MetricsAPIView.as_view(), name="metrics"),
    re_path(r"^api/schema/?$", SpectacularAPIView.as_view(), name="schema"),
    re_path(
        r"^api/docs/?$",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
