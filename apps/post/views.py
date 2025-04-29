from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Post
from .serializers import PostSerializer, PostCreateSerializer, PostUpdateSerializer

class PostViewSet(viewsets.ModelViewSet):
    """게시물 뷰셋"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """게시물 목록을 반환합니다."""
        return Post.objects.filter(is_deleted=False)
    
    def get_serializer_class(self):
        """액션에 따라 적절한 시리얼라이저를 반환합니다."""
        if self.action == 'create':
            return PostCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PostUpdateSerializer
        return PostSerializer
    
    def perform_create(self, serializer):
        """게시물을 생성합니다."""
        serializer.save(author=self.request.user)
    
    def perform_update(self, serializer):
        """게시물을 수정합니다."""
        post = self.get_object()
        if post.author != self.request.user:
            return Response(
                {"detail": "게시물을 수정할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()
    
    def perform_destroy(self, instance):
        """게시물을 소프트 삭제합니다."""
        if instance.author != self.request.user:
            return Response(
                {"detail": "게시물을 삭제할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.soft_delete(self.request.user)
    
    @action(detail=True, methods=['post'])
    def increase_views(self, request, pk=None):
        """조회수를 증가시킵니다."""
        post = self.get_object()
        post.increase_views()
        return Response(PostSerializer(post).data)
    
    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """삭제된 게시물을 복구합니다."""
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {"detail": "게시물을 복구할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )
        post.restore()
        return Response(PostSerializer(post).data)
