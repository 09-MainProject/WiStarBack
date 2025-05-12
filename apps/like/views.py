from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.post.models import Post
from utils.exceptions import CustomAPIException

from .models import Like
from .serializers import LikeSerializer


class LikeView(APIView):
    """좋아요 View"""

    permission_classes = [IsAuthenticated]
    allowed_methods = ["GET", "POST", "DELETE"]

    @swagger_auto_schema(
        tags=["likes"],
        operation_summary="좋아요 생성",
        operation_description="게시물에 좋아요를 추가합니다.",
        responses={
            201: "좋아요 생성 성공",
            401: "인증되지 않은 사용자",
            404: "게시물을 찾을 수 없음",
        },
    )
    def post(self, request, post_id):
        """좋아요를 생성합니다."""
        post = get_object_or_404(Post, id=post_id)

        try:
            like, created = Like.objects.get_or_create(post=post, user=request.user)

            if not created:
                like.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            return Response(status=status.HTTP_201_CREATED)

        except Exception as e:
            raise CustomAPIException(
                {
                    "code": 500,
                    "message": "An error occurred while processing the like.",
                    "data": None,
                }
            )

    @swagger_auto_schema(
        tags=["likes"],
        operation_summary="좋아요 목록 조회",
        operation_description="게시물의 좋아요 목록을 조회합니다.",
        responses={
            200: "좋아요 목록 조회 성공",
            401: "인증되지 않은 사용자",
            404: "게시물을 찾을 수 없음",
        },
    )
    def get(self, request, post_id):
        """좋아요 목록을 조회합니다."""
        post = get_object_or_404(Post, id=post_id)
        likes = Like.objects.filter(post=post)
        serializer = LikeSerializer(likes, many=True)
        return Response(
            {
                "code": 200,
                "message": "Likes list retrieved successfully",
                "data": serializer.data,
            }
        )

    @swagger_auto_schema(
        tags=["likes"],
        operation_summary="좋아요 삭제",
        operation_description="게시물의 좋아요를 삭제합니다.",
        responses={
            200: "좋아요 삭제 성공",
            401: "인증되지 않은 사용자",
            404: "게시물 또는 좋아요를 찾을 수 없음",
        },
    )
    def delete(self, request, post_id):
        """게시글의 좋아요를 취소합니다."""
        post = get_object_or_404(Post, id=post_id)
        like = get_object_or_404(Like, post=post, user=request.user)
        like.delete()

        return Response(
            {"code": 200, "message": "Like deleted successfully", "data": None}
        )


class LikeStatusView(APIView):
    """좋아요 상태 조회 View"""

    permission_classes = [IsAuthenticated]
    allowed_methods = ["GET"]

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
