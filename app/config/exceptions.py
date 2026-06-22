import logging

from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    request = context.get("request")

    logger.warning(
        "api exception handled",
        exc_info=exc,
        extra={
            "method": getattr(request, "method", None),
            "path": request.get_full_path() if request else None,
            "status_code": getattr(response, "status_code", 500),
        },
    )

    if response is not None:
        return response

    logger.exception("unhandled api exception", exc_info=exc)
    return response
