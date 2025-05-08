from django.contrib.contenttypes.models import ContentType
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from utils.exceptions import CustomAPIException

from .models import Like
from .serializers import LikeSerializer


class LikeViewSet(viewsets.ModelViewSet):
    """좋아요 뷰셋"""

    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """권한을 설정합니다."""
        if not self.request.user.is_authenticated:
            message = {
                "create": "좋아요를 누르려면 로그인이 필요합니다.",
                "destroy": "좋아요를 취소하려면 로그인이 필요합니다.",
                "like_status": "좋아요 상태를 확인하려면 로그인이 필요합니다.",
            }.get(self.action, "로그인이 필요한 서비스입니다.")

            raise CustomAPIException({"code": 401, "message": message, "data": None})
        return [IsAuthenticated()]

    def get_queryset(self):
        """좋아요 목록을 반환합니다."""
        content_type = ContentType.objects.get(
            app_label=self.kwargs.get("app_label"),
            model=self.kwargs.get("app_label"),  # app_label을 model로도 사용
        )
        object_id = self.kwargs.get("object_id")
        return Like.objects.filter(content_type=content_type, object_id=object_id)

    @swagger_auto_schema(
        operation_summary="좋아요 생성",
        operation_description="좋아요를 추가합니다.",
        tags=["좋아요"],
        responses={
            201: openapi.Response(
                description="게시글/댓글 좋아요 성공.",
                examples={
                    "application/json": {
                        "code": 201,
                        "message": "게시글/댓글 좋아요 성공.",
                        "data": {"like_id": 1},
                    }
                },
            ),
            400: openapi.Response(
                description="이미 좋아요를 눌렀습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "이미 좋아요를 눌렀습니다.",
                        "data": {"like_id": 12},
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None,
                    }
                },
            ),
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        """좋아요를 생성합니다."""
        content_type = ContentType.objects.get(
            app_label=self.kwargs.get("app_label", "post"),
            model=self.kwargs.get("model", "post"),
        )
        object_id = self.kwargs.get("object_id")
        serializer.save(
            user=self.request.user, content_type=content_type, object_id=object_id
        )

    @swagger_auto_schema(
        operation_summary="좋아요 삭제",
        operation_description="좋아요를 취소합니다.",
        tags=["좋아요"],
        responses={
            204: openapi.Response(
                description="게시글/댓글 좋아요 취소 성공.",
                examples={
                    "application/json": {
                        "code": 204,
                        "message": "게시글/댓글 좋아요 취소 성공.",
                        "data": None,
                    }
                },
            ),
            400: openapi.Response(
                description="좋아요 취소에 실패하였습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "좋아요 취소에 실패하였습니다.",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None,
                    }
                },
            ),
        },
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        instance.delete()
        return Response(
            {"code": 204, "message": "게시글/댓글 좋아요 취소 성공.", "data": None},
            status=status.HTTP_204_NO_CONTENT,
        )

    @swagger_auto_schema(
        operation_summary="좋아요 상태 조회",
        operation_description="좋아요 상태를 반환합니다.",
        tags=["좋아요"],
        responses={
            200: openapi.Response(
                description="좋아요 조회 성공.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "좋아요 조회 성공.",
                        "data": {"liked": True},
                    }
                },
            ),
            400: openapi.Response(
                description="좋아요 정보를 찾을 수 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "좋아요 정보를 찾을 수 없습니다.",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None,
                    }
                },
            ),
        },
    )
    @action(detail=False, methods=["get"])
    def like_status(self, request, app_label=None, model=None, object_id=None):
        content_type = ContentType.objects.get(app_label=app_label, model=model)
        exists = Like.objects.filter(
            content_type=content_type, object_id=object_id, user=request.user
        ).exists()
        return Response({"liked": exists})
