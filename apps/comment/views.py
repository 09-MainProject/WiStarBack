from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as django_filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.like.models import Like
from apps.post.models import Post
from utils.exceptions import CustomAPIException

from .models import Comment
from .serializers import (
    CommentCreateSerializer,
    CommentSerializer,
    CommentUpdateSerializer,
)


class CommentPagination(PageNumberPagination):
    """댓글 페이지네이션"""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class CommentFilter(django_filters.FilterSet):
    """댓글 필터"""

    content = django_filters.CharFilter(lookup_expr="icontains")
    created_at = django_filters.DateTimeFilter(lookup_expr="gte")
    created_at_end = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )
    parent = django_filters.NumberFilter(field_name="parent", lookup_expr="isnull")

    class Meta:
        model = Comment
        fields = ["content", "created_at", "created_at_end", "parent"]


class CommentViewSet(viewsets.ModelViewSet):
    """댓글 뷰셋 (댓글/대댓글 통합)"""

    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Comment.objects.filter(is_deleted=False)
    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = CommentFilter
    search_fields = ["content"]
    ordering_fields = ["created_at"]
    ordering = ["-created_at"]
    pagination_class = CommentPagination
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """post_id에 해당하는 게시물의 댓글만 필터링합니다."""
        queryset = super().get_queryset()
        post_id = self.kwargs.get("post_id")
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def get_serializer_context(self):
        """시리얼라이저 컨텍스트에 post_id를 추가합니다."""
        context = super().get_serializer_context()
        context["post_id"] = self.kwargs.get("post_id")
        return context

    def get_serializer_class(self):
        """액션에 따라 적절한 시리얼라이저를 반환합니다."""
        if self.action == "create":
            return CommentCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return CommentUpdateSerializer
        return CommentSerializer

    def perform_create(self, serializer):
        """댓글을 생성합니다."""
        post_id = self.kwargs.get("post_id")
        post = get_object_or_404(Post, id=post_id)

        # 대댓글인 경우 부모 댓글 확인
        parent_id = self.request.data.get("parent")
        if parent_id:
            parent = get_object_or_404(Comment, id=parent_id, post=post)
            if parent.parent is not None:
                raise CustomAPIException(
                    {
                        "code": 400,
                        "message": "대댓글에는 답글을 달 수 없습니다.",
                        "data": None,
                    }
                )
            comment = serializer.save(
                author=self.request.user, post=post, parent=parent
            )
        else:
            comment = serializer.save(author=self.request.user, post=post)
        return comment

    @swagger_auto_schema(
        operation_summary="댓글 목록 조회",
        operation_description="댓글 목록을 조회합니다.",
        tags=["comments"],
        responses={
            200: openapi.Response(
                description="댓글 목록 조회 성공",
                schema=CommentSerializer,
            ),
            400: openapi.Response(
                description="잘못된 요청",
                examples={"application/json": {"detail": "잘못된 요청입니다."}},
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        """댓글 목록을 반환합니다."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(
                    page, many=True, context={"request": request}
                )
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(
                queryset, many=True, context={"request": request}
            )
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="댓글 생성",
        operation_description="새로운 댓글을 생성합니다.",
        tags=["comments"],
        responses={
            201: openapi.Response(
                description="댓글 작성 성공",
                schema=CommentSerializer,
            ),
            400: openapi.Response(
                description="댓글 작성 실패",
                examples={"application/json": {"detail": "댓글 작성에 실패했습니다."}},
            ),
        },
    )
    def create(self, request, *args, **kwargs):
        """댓글을 생성합니다."""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            comment = self.perform_create(serializer)
            response_serializer = CommentSerializer(
                comment, context={"request": request}
            )
            headers = self.get_success_headers(serializer.data)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
                headers=headers,
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_summary="댓글 부분 수정",
        operation_description="댓글의 일부 정보를 수정합니다.",
        tags=["comments"],
        responses={
            200: openapi.Response(
                description="댓글 수정 성공",
                schema=CommentSerializer,
            ),
            400: openapi.Response(
                description="수정 권한 없음",
                examples={
                    "application/json": {"detail": "댓글을 수정할 권한이 없습니다."}
                },
            ),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        """댓글을 부분 수정합니다."""
        instance = self.get_object()
        if instance.author != request.user:
            raise PermissionDenied("댓글을 수정할 권한이 없습니다.")
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="댓글 삭제",
        operation_description="댓글을 삭제합니다.",
        tags=["comments"],
        responses={
            204: openapi.Response(
                description="댓글 삭제 성공",
                examples={"application/json": {"detail": "댓글이 삭제되었습니다."}},
            ),
            400: openapi.Response(
                description="삭제 권한 없음",
                examples={
                    "application/json": {"detail": "댓글을 삭제할 권한이 없습니다."}
                },
            ),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """댓글을 삭제합니다."""
        instance = self.get_object()
        if instance.author != request.user:
            raise PermissionDenied("댓글을 삭제할 권한이 없습니다.")
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post", "delete"], url_path="likes")
    def likes(self, request, pk=None):
        """댓글 좋아요/취소 API (POST: 좋아요, DELETE: 좋아요 취소)"""
        comment = self.get_object()
        user = request.user
        content_type = ContentType.objects.get_for_model(comment)

        if request.method == "POST":
            # 이미 좋아요가 있으면 아무 변화 없음
            like, created = Like.objects.get_or_create(
                content_type=content_type, object_id=comment.id, user=user
            )
            return Response(
                {"status": "liked"},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        elif request.method == "DELETE":
            deleted, _ = Like.objects.filter(
                content_type=content_type, object_id=comment.id, user=user
            ).delete()
            return Response(
                {"status": "unliked"},
                status=status.HTTP_204_NO_CONTENT if deleted else status.HTTP_200_OK,
            )

    @action(detail=True, methods=["get"], url_path="like-status")
    def like_status(self, request, pk=None):
        """댓글 좋아요 상태 조회 API"""
        comment = self.get_object()
        user = request.user
        content_type = ContentType.objects.get_for_model(comment)

        is_liked = Like.objects.filter(
            content_type=content_type, object_id=comment.id, user=user
        ).exists()

        # 좋아요한 사용자 목록
        liked_users = (
            Like.objects.filter(content_type=content_type, object_id=comment.id)
            .select_related("user")
            .values_list("user__nickname", flat=True)
        )

        return Response(
            {
                "is_liked": is_liked,
                "likes_count": comment.likes.count(),
                "liked_users": list(liked_users),
            }
        )


class CommentView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        tags=["comments"],
        operation_description="특정 게시물의 댓글 목록을 조회합니다.",
        responses={
            200: openapi.Response(
                description="댓글 목록 조회 성공",
                schema=CommentSerializer,
            ),
            401: openapi.Response(
                description="인증되지 않은 사용자",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                },
            ),
            404: openapi.Response(
                description="게시물을 찾을 수 없음",
                examples={"application/json": {"detail": "Not found."}},
            ),
        },
    )
    def get(self, request, post_id):
        comments = Comment.objects.filter(
            post_id=post_id, parent=None, is_deleted=False
        ).order_by("created_at")
        serializer = CommentSerializer(
            comments, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @swagger_auto_schema(
        tags=["comments"],
        operation_description="새로운 댓글을 생성합니다.",
        request_body=CommentCreateSerializer(),
        responses={
            201: openapi.Response(
                description="댓글 생성 성공",
                schema=CommentSerializer,
            ),
            400: openapi.Response(
                description="잘못된 요청",
                examples={"application/json": {"detail": "잘못된 요청입니다."}},
            ),
            401: openapi.Response(
                description="인증되지 않은 사용자",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                },
            ),
            404: openapi.Response(
                description="게시물을 찾을 수 없음",
                examples={"application/json": {"detail": "Not found."}},
            ),
        },
    )
    def post(self, request, post_id):
        serializer = CommentCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(author=request.user, post_id=post_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, comment_id):
        return get_object_or_404(Comment, id=comment_id, is_deleted=False)

    @swagger_auto_schema(
        tags=["comments"],
        operation_description="특정 댓글을 수정합니다.",
        request_body=CommentUpdateSerializer(),
        responses={
            200: openapi.Response(
                description="댓글 수정 성공",
                schema=CommentSerializer,
            ),
            400: openapi.Response(
                description="잘못된 요청",
                examples={"application/json": {"detail": "잘못된 요청입니다."}},
            ),
            401: openapi.Response(
                description="인증되지 않은 사용자",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                },
            ),
            403: openapi.Response(
                description="권한 없음",
                examples={"application/json": {"detail": "권한이 없습니다."}},
            ),
            404: openapi.Response(
                description="댓글을 찾을 수 없음",
                examples={"application/json": {"detail": "Not found."}},
            ),
        },
    )
    def put(self, request, comment_id):
        comment = self.get_object(comment_id)
        if comment.author != request.user:
            return Response(
                {"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )
        serializer = CommentUpdateSerializer(comment, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=["comments"],
        operation_description="특정 댓글을 삭제합니다.",
        responses={
            204: openapi.Response(
                description="댓글 삭제 성공",
                examples={"application/json": {"detail": "댓글이 삭제되었습니다."}},
            ),
            401: openapi.Response(
                description="인증되지 않은 사용자",
                examples={
                    "application/json": {
                        "detail": "Authentication credentials were not provided."
                    }
                },
            ),
            403: openapi.Response(
                description="권한 없음",
                examples={"application/json": {"detail": "권한이 없습니다."}},
            ),
            404: openapi.Response(
                description="댓글을 찾을 수 없음",
                examples={"application/json": {"detail": "Not found."}},
            ),
        },
    )
    def delete(self, request, comment_id):
        comment = self.get_object(comment_id)
        if comment.author != request.user:
            return Response(
                {"detail": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN
            )
        comment.is_deleted = True
        comment.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
