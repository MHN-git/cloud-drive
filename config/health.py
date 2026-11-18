from django.db import connection
from django.http import JsonResponse
from django_redis import get_redis_connection
from django.views.decorators.http import require_GET

from files.minio_client import get_minio_client
from django.conf import settings


@require_GET
def live(request):
    return JsonResponse({"status": "ok"})


@require_GET
def ready(request):
    checks = {}

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "error"

    try:
        get_redis_connection("default").ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    try:
        client = get_minio_client()
        if client.bucket_exists(settings.MINIO_BUCKET):
            checks["minio"] = "ok"
        else:
            checks["minio"] = "error"
    except Exception:
        checks["minio"] = "error"

    is_ready = all(status == "ok" for status in checks.values())

    return JsonResponse(
        {
            "status": "ok" if is_ready else "error",
            "checks": checks,
        },
        status=200 if is_ready else 503,
    )