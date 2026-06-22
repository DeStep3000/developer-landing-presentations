import logging
import time

request_logger = logging.getLogger("requests")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started_at = time.perf_counter()
        response = self.get_response(request)
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)

        request_logger.info(
            "request handled",
            extra={
                "method": request.method,
                "path": request.get_full_path(),
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
