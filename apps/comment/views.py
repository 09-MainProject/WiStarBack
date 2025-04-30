from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as django_filters
from .models import Comment
from .serializers import CommentSerializer, CommentCreateSerializer, CommentUpdateSerializer
from apps.post.models import Post

class CommentFilter(django_filters.FilterSet):
    """댓글 필터"""
    content = django_filters.CharFilter(lookup_expr='icontains')
    created_at = django_filters.DateTimeFilter(lookup_expr='gte')
    created_at_end = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Comment
        fields = ['content', 'created_at', 'created_at_end']

class CommentViewSet(viewsets.ModelViewSet):
    """댓글 뷰셋"""
    filter_backends = [django_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CommentFilter
    search_fields = ['content']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_permissions(self):
        """
        액션에 따라 권한을 설정합니다.
        - 조회(GET): 모든 사용자 가능
        - 생성(POST), 수정(PATCH), 삭제(DELETE): 인증된 사용자만 가능
        """
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        """댓글 목록을 반환합니다."""
        post_id = self.kwargs.get('post_pk')
        return Comment.objects.filter(post_id=post_id, is_deleted=False)
    
    def get_serializer_class(self):
        """액션에 따라 적절한 시리얼라이저를 반환합니다."""
        if self.action == 'create':
            return CommentCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CommentUpdateSerializer
        return CommentSerializer
    
    def perform_create(self, serializer):
        """댓글을 생성합니다."""
        post_id = self.kwargs.get('post_pk')
        post = get_object_or_404(Post, id=post_id)
        serializer.save(author=self.request.user, post=post)
    
    def perform_update(self, serializer):
        """댓글을 수정합니다."""
        comment = self.get_object()
        if comment.author != self.request.user:
            raise PermissionDenied("댓글을 수정할 권한이 없습니다.")
        serializer.save()
    
    def perform_destroy(self, instance):
        """댓글을 소프트 삭제합니다."""
        if instance.author != self.request.user:
            raise PermissionDenied("댓글을 삭제할 권한이 없습니다.")
        instance.soft_delete(self.request.user) 