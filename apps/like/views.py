from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.post.models import Post
from utils.exceptions import CustomAPIException

from .models import Like
from .serializers import LikeSerializer


class LikeView(ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LikeSerializer

    def get_queryset(self):
        type = self.kwargs.get('type')
        id = self.kwargs.get('id')
        content_type = ContentType.objects.get(model=type)
        return Like.objects.filter(content_type=content_type, object_id=id)

    def perform_create(self, serializer):
        type = self.kwargs.get('type')
        id = self.kwargs.get('id')
        content_type = ContentType.objects.get(model=type)
        serializer.save(user=self.request.user, content_type=content_type, object_id=id)


class LikeStatusView(RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LikeSerializer

    def get_object(self):
        type = self.kwargs.get('type')
        id = self.kwargs.get('id')
        content_type = ContentType.objects.get(model=type)
        return Like.objects.filter(
            user=self.request.user,
            content_type=content_type,
            object_id=id
        ).first()


class LikeStatusView(APIView):
    """좋아요 상태 조회 View"""

    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    @swagger_auto_schema(
        tags=["likes"],
        operation_summary="좋아요 상태 조회",
        operation_description="현재 사용자의 게시물 좋아요 상태와 총 좋아요 수를 확인합니다.",
        responses={
            200: "좋아요 상태 조회 성공",
            401: "인증되지 않은 사용자",
            404: "게시물을 찾을 수 없음",
        },
    )
    def get(self, request, post_id):
        """좋아요 상태를 조회합니다."""
        post = get_object_or_404(Post, id=post_id)

        is_liked = Like.objects.filter(post=post, user=request.user).exists()
        likes_count = Like.objects.filter(post=post).count()

        return Response(
            {
                "code": 200,
                "message": "Like status retrieved successfully",
                "data": {"is_liked": is_liked, "likes_count": likes_count},
            }
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
    def like_status(self, request, type=None, id=None):
        content_type = ContentType.objects.get(app_label=type, model=type)
        exists = Like.objects.filter(
            content_type=content_type, object_id=id, user=request.user
        ).exists()
        return Response({"liked": exists})
