from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.exceptions import (
    APIException,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
)
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    # DRF 기본 핸들러 호출
    response = exception_handler(exc, context)

    # 기본 응답이 있는 경우 (DRF가 처리 가능한 경우)
    if response is not None:
        status_code = response.status_code

        # 1. DRF ValidationError (serializer.is_valid())
        if isinstance(exc, ValidationError):
            if isinstance(response.data, dict):
                field, messages = next(iter(response.data.items()))
                message = messages[0] if isinstance(messages, list) else str(messages)
            else:
                message = str(response.data)
            response.data = {
                "code": status_code,
                "message": message,
                "data": response.data,  # 전체 오류 딕셔너리
            }
            return response

        # 2. CustomAPIException (detail이 dict 형태일 경우)
        if isinstance(exc, APIException):
            if isinstance(exc.detail, dict):
                # 이미 커스텀 구조라면 그대로 사용
                response.data = exc.detail
            else:
                response.data = {
                    "code": status_code,
                    "message": str(exc.detail),
                    "data": None,
                }
            return response

    # DRF 기본 핸들러가 처리 못한 예외 (response is None)
    else:
        # 3. Django ValidationError (ex. validate_password)
        if isinstance(exc, DjangoValidationError):
            return _format_response(400, "유효성 검사 실패", list(exc.messages))

        # 4. IntegrityError (중복 등)
        if isinstance(exc, IntegrityError):
            return _format_response(400, "데이터베이스 무결성 오류", str(exc))

        # 5. 인증 오류 등 (NotAuthenticated, PermissionDenied)
        if isinstance(exc, (NotAuthenticated, PermissionDenied)):
            return _format_response(403, "권한이 없습니다.", str(exc))

        # 6. 기타 예상 못한 예외
        return _format_response(500, "서버 내부 오류가 발생했습니다.", str(exc))

    return response  # fallback


# 응답 포맷 헬퍼 함수
from rest_framework.response import Response


def _format_response(code, message, data=None):
    return Response({"code": code, "message": message, "data": data}, status=code)


# 각 필드의 의미와 이유
# 필드         설명                             이유
# code        HTTP 상태 코드                    프론트가 200/400/403/500을 직접 분기 처리하기 좋음
# message     사용자에게 보여줄 핵심 메시지          단일 메시지로 alert / toast에 바로 활용
# data        상세 에러, 필드별 메시지 등           폼 필드별 에러 표시 등에 활용 (예: email, password)


# from rest_framework.views import exception_handler
# from rest_framework.exceptions import ValidationError
#
# 커스텀 에러 헨들러
# def custom_exception_handler(exc, context):
#     response = exception_handler(exc, context)
#
#     if isinstance(exc, ValidationError) and response is not None:
#         error_dict = response.data
#         # 첫 번째 필드와 메시지만 가져옴
#         if isinstance(error_dict, dict):
#             first_field, messages = next(iter(error_dict.items()))
#             message = messages[0] if isinstance(messages, list) else str(messages)
#         else:
#             message = str(error_dict)
#
#         response.data = {
#             "code": 400,
#             "message": message,
#             "data": None
#         }
#
#     return response
