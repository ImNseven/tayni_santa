from django.core.cache import cache
from django.db import connections
from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


def _check_database() -> bool:
    try:
        with connections["default"].cursor() as cursor:
            cursor.execute("SELECT 1")
            return cursor.fetchone() == (1,)
    except Exception:
        return False


def _check_cache() -> bool:
    try:
        cache.set("healthcheck", "ok", timeout=5)
        return cache.get("healthcheck") == "ok"
    except Exception:
        return False


@extend_schema(
    summary="Health check",
    responses=inline_serializer(
        name="HealthResponse",
        fields={
            "status": serializers.CharField(),
            "checks": inline_serializer(
                name="HealthChecks",
                fields={
                    "database": serializers.CharField(),
                    "cache": serializers.CharField(),
                },
            ),
        },
    ),
    examples=[
        OpenApiExample(
            "healthy",
            value={"status": "ok", "checks": {"database": "ok", "cache": "ok"}},
        )
    ],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    checks = {
        "database": "ok" if _check_database() else "error",
        "cache": "ok" if _check_cache() else "error",
    }
    healthy = all(v == "ok" for v in checks.values())
    return Response(
        {"status": "ok" if healthy else "degraded", "checks": checks},
        status=status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE,
    )
