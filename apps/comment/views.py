from django.shortcuts import get_object_or_404
from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from utils.exceptions import CustomAPIException
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from apps.post.models import Post

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

    class Meta:
        model = Comment
        fields = ["content", "created_at", "created_at_end"]


class CommentViewSet(viewsets.ModelViewSet):
    """댓글 뷰셋"""

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

    def get_queryset(self):
        """post_id에 해당하는 게시물의 댓글만 필터링합니다."""
        queryset = super().get_queryset()
        post_id = self.kwargs.get("post_id")
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        return queryset

    def get_permissions(self):
        """
        액션에 따라 권한을 설정합니다.
        - 조회(GET): 모든 사용자 가능
        - 생성(POST), 수정(PATCH), 삭제(DELETE): 인증된 사용자만 가능
        """
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        
        if not self.request.user.is_authenticated:
            message = {
                "create": "댓글을 작성하려면 로그인이 필요합니다.",
                "update": "댓글을 수정하려면 로그인이 필요합니다.",
                "partial_update": "댓글을 수정하려면 로그인이 필요합니다.",
                "destroy": "댓글을 삭제하려면 로그인이 필요합니다.",
            }.get(self.action, "로그인이 필요한 서비스입니다.")
            
            raise CustomAPIException({
                "code": 401,
                "message": message,
                "data": None
            })
        return [IsAuthenticated()]

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
        comment = serializer.save(author=self.request.user, post=post)
        return comment

    @swagger_auto_schema(
        operation_summary="댓글 검색",
        operation_description="댓글을 검색합니다.",
        tags=["댓글"],
        responses={
            200: openapi.Response(
                description="댓글 검색 성공",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "댓글 검색 성공.",
                        "data": [
                            {"comment_id": 11, "post_id": 123, "user_id": 42, "content": "아이브 정말 응원해요!"},
                            {"comment_id": 15, "post_id": 123, "user_id": 88, "content": "항상 응원해요!"}
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="댓글 정보를 찾을 수 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "댓글 정보를 찾을 수 없습니다.",
                        "data": None
                    }
                }
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None
                    }
                }
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="댓글 생성",
        operation_description="댓글을 생성합니다.",
        tags=["댓글"],
        responses={
            201: openapi.Response(
                description="댓글 작성 성공.",
                examples={
                    "application/json": {
                        "code": 201,
                        "message": "댓글 작성 성공.",
                        "data": {"comment_id": 1}
                    }
                }
            ),
            400: openapi.Response(
                description="댓글 작성이 실패하였습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "댓글 작성이 실패하였습니다.",
                        "data": None
                    }
                }
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None
                    }
                }
            )
        }
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = self.perform_create(serializer)
        response_serializer = CommentSerializer(comment)
        headers = self.get_success_headers(serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @swagger_auto_schema(
        operation_summary="댓글 상세",
        operation_description="댓글 상세 정보를 조회합니다.",
        tags=["댓글"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="댓글 수정",
        operation_description="댓글을 수정합니다.",
        tags=["댓글"],
        responses={
            200: openapi.Response(
                description="댓글 수정 성공.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "댓글 수정 성공.",
                        "data": {"comment_id": 1}
                    }
                }
            ),
            400: openapi.Response(
                description="수정 권한이 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "수정 권한이 없습니다.",
                        "data": None
                    }
                }
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None
                    }
                }
            )
        }
    )
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        if instance.author != request.user and not request.user.is_staff:
            raise PermissionDenied("댓글을 수정할 권한이 없습니다.")
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        response_serializer = CommentSerializer(instance)
        return Response(response_serializer.data)

    @swagger_auto_schema(
        operation_summary="댓글 부분 수정",
        operation_description="댓글을 부분 수정합니다.",
        tags=["댓글"],
        responses={
            200: openapi.Response(
                description="댓글 수정 성공.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "댓글 수정 성공.",
                        "data": {"comment_id": 1}
                    }
                }
            ),
            400: openapi.Response(
                description="수정 권한이 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "수정 권한이 없습니다.",
                        "data": None
                    }
                }
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None
                    }
                }
            )
        }
    )
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="댓글 삭제",
        operation_description="댓글을 삭제합니다.",
        tags=["댓글"],
        responses={
            204: openapi.Response(
                description="댓글 삭제 성공.",
                examples={
                    "application/json": {
                        "code": 204,
                        "message": "댓글 삭제 성공.",
                        "data": None
                    }
                }
            ),
            400: openapi.Response(
                description="삭제 권한이 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "삭제 권한이 없습니다.",
                        "data": None
                    }
                }
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None
                    }
                }
            )
        }
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("댓글을 삭제할 권한이 없습니다.")
        instance.soft_delete(self.request.user)
        return Response({
            "code": 204,
            "message": "댓글 삭제 성공.",
            "data": None
        }, status=status.HTTP_204_NO_CONTENT)
