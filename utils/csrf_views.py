from django.http import JsonResponse

from utils.responses.user import CSRF_INVALID_TOKEN


def csrf_failure_view(request, reason=""):
    return JsonResponse({
        **CSRF_INVALID_TOKEN,
        "reason": reason,  # 원인 문자열 (선택)
    }, status=403)