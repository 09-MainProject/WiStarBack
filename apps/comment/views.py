from django.shortcuts import get_object_or_404
from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

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

    def create(self, request, *args, **kwargs):
        """댓글을 생성하고 전체 정보를 반환합니다."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = self.perform_create(serializer)
        response_serializer = CommentSerializer(comment)
        headers = self.get_success_headers(serializer.data)
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_update(self, serializer):
        """댓글을 수정합니다."""
        comment = self.get_object()
        if comment.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("댓글을 수정할 권한이 없습니다.")
        serializer.save()

    def perform_destroy(self, instance):
        """댓글을 소프트 삭제합니다."""
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("댓글을 삭제할 권한이 없습니다.")
        instance.soft_delete(self.request.user)
