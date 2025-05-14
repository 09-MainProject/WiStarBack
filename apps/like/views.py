from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.post.models import Post
from apps.comment.models import Comment
from utils.exceptions import CustomAPIException

from .models import Like
from .serializers import LikeSerializer


class LikeView(APIView):
    """좋아요 View"""
    permission_classes = [IsAuthenticated]
    http_method_names = ["post", "delete"]

    @swagger_auto_schema(
        tags=["좋아요"],
        operation_summary="좋아요 생성",
        operation_description="게시글/댓글에 좋아요를 추가합니다.",
        responses={
            201: "좋아요 생성 성공",
            401: "인증되지 않은 사용자",
            404: "게시글/댓글을 찾을 수 없음",
        },
    )
    def post(self, request, id):
        """좋아요를 생성합니다."""
        # posts 또는 comments 구분
        if "posts" in request.path:
            target = get_object_or_404(Post, id=id)
            content_type = ContentType.objects.get_for_model(Post)
        elif "comments" in request.path:
            target = get_object_or_404(Comment, id=id)
            content_type = ContentType.objects.get_for_model(Comment)
        else:
            return Response({"code": 400, "message": "잘못된 요청입니다.", "data": None}, status=400)

        like, created = Like.objects.get_or_create(
            user=request.user,
            content_type=content_type,
            object_id=id
        )
        if not created:
            return Response({"code": 400, "message": "이미 좋아요를 누른 상태입니다.", "data": None}, status=400)
        return Response({"code": 201, "message": "좋아요 생성 성공.", "data": {"like_id": like.id}}, status=201)

    @swagger_auto_schema(
        tags=["좋아요"],
        operation_summary="좋아요 삭제",
        operation_description="게시글/댓글의 좋아요를 삭제합니다.",
        responses={
            204: "좋아요 삭제 성공",
            401: "인증되지 않은 사용자",
            404: "게시글/댓글 또는 좋아요를 찾을 수 없음",
        },
    )
    def delete(self, request, id):
        if "posts" in request.path:
            content_type = ContentType.objects.get_for_model(Post)
        elif "comments" in request.path:
            content_type = ContentType.objects.get_for_model(Comment)
        else:
            return Response({"code": 400, "message": "잘못된 요청입니다.", "data": None}, status=400)
        like = Like.objects.filter(
            user=request.user,
            content_type=content_type,
            object_id=id
        ).first()
        if not like:
            return Response({"code": 404, "message": "좋아요를 찾을 수 없습니다.", "data": None}, status=404)
        like.delete()
        return Response({"code": 204, "message": "좋아요 삭제 성공.", "data": None}, status=204)


class LikeStatusView(APIView):
    """좋아요 여부(상태) 조회"""
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    @swagger_auto_schema(
        operation_summary="좋아요 여부(상태) 조회",
        operation_description="게시글/댓글의 좋아요 여부를 반환합니다.",
        tags=["좋아요"],
        responses={
            200: openapi.Response(
                description="좋아요 조회 성공.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "좋아요 조회 성공.",
                        "data": {
                            "liked": True
                        }
                    }
                },
            ),
            400: openapi.Response(
                description="좋아요 정보를 찾을 수 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "좋아요 정보를 찾을 수 없습니다.",
                        "data": None
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None
                    }
                },
            ),
        },
    )
    def get(self, request, type, id):
        try:
            if type == "posts":
                content_type = ContentType.objects.get_for_model(Post)
            elif type == "comments":
                content_type = ContentType.objects.get_for_model(Comment)
            else:
                return Response(
                    {
                        "code": 400,
                        "message": "좋아요 정보를 찾을 수 없습니다.",
                        "data": None
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            liked = Like.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=id
            ).exists()
            return Response(
                {
                    "code": 200,
                    "message": "좋아요 조회 성공.",
                    "data": {"liked": liked}
                }
            )
        except Exception:
            return Response(
                {
                    "code": 500,
                    "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                    "data": None
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
