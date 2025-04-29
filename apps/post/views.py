from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.renderers import JSONRenderer
from django_filters import rest_framework as filters
from rest_framework import filters as drf_filters
from .models import Post, Comment
from .serializers import PostSerializer, CommentSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from .pagination import PostPagination, CommentPagination

class PostFilter(filters.FilterSet):
    """게시물 필터"""
    title = filters.CharFilter(lookup_expr='icontains')
    content = filters.CharFilter(lookup_expr='icontains')
    created_at = filters.DateTimeFilter(lookup_expr='gte')
    created_at_end = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    author = filters.NumberFilter()  # 작성자 ID로 필터링

    class Meta:
        model = Post
        fields = ['title', 'content', 'created_at', 'created_at_end', 'author']


class PostViewSet(ModelViewSet):
    """
    게시물 정보 관리 뷰셋

    list:
    게시물 목록 조회

    create:
    새 게시물 생성

    retrieve:
    게시물 상세 정보 조회

    partial_update:
    게시물 정보 부분 수정

    destroy:
    게시물 삭제
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter]
    filterset_class = PostFilter
    ordering_fields = ['created_at', 'views']
    ordering = ['-created_at']
    search_fields = ['title', 'content']
    pagination_class = PostPagination
    http_method_names = ['get', 'post', 'patch', 'delete']  # PUT 제거, PATCH만 허용

    def get_queryset(self):
        """삭제되지 않은 게시물만 조회"""
        return Post.objects.filter(is_deleted=False)

    def get_permissions(self):
        """
        HTTP 메서드별 권한 설정
        - GET: 모든 사용자 가능
        - POST, PATCH, DELETE: 로그인한 사용자만 가능
        """
        if self.action in ['create', 'partial_update', 'destroy', 'increase_views']:
            return [IsAuthenticated()]
        return [IsAuthenticatedOrReadOnly()]

    def perform_create(self, serializer):
        """게시물 생성 시 작성자 정보 추가"""
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """게시물 수정 시 작성자 확인"""
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("게시물을 수정할 권한이 없습니다.")
        serializer.save()

    def perform_destroy(self, instance):
        """게시물 삭제 시 작성자 확인 후 소프트 삭제"""
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("게시물을 삭제할 권한이 없습니다.")
        instance.soft_delete(self.request.user)

    @action(detail=True, methods=['post'])
    def increase_views(self, request, pk=None):
        """게시물 조회수 증가"""
        post = self.get_object()
        post.increase_views()
        return Response({"views": post.views})


class PostListByAuthorView(generics.ListAPIView):
    """
    작성자별 게시물 목록 조회 뷰

    GET: 작성자별 게시물 목록 조회
    """
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = PostFilter
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'views']
    ordering = ['-created_at']
    pagination_class = PostPagination

    def get_queryset(self):
        """작성자별 게시물 목록 조회"""
        author_id = self.kwargs.get('author_id')
        return Post.objects.filter(author_id=author_id, is_deleted=False)


class CommentListCreateView(generics.ListCreateAPIView):
    """
    댓글 목록 조회 및 생성 뷰
    
    GET: 댓글 목록 조회
    POST: 새 댓글 생성
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['post', 'parent']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    pagination_class = CommentPagination

    def get_permissions(self):
        """
        HTTP 메서드별 권한 설정
        - GET: 모든 사용자 가능
        - POST: 로그인한 사용자만 가능
        """
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """특정 게시물의 댓글만 조회"""
        post_id = self.kwargs.get('post_id')
        return Comment.objects.filter(post_id=post_id, is_deleted=False)

    def perform_create(self, serializer):
        """댓글 생성 시 작성자 정보 추가"""
        post_id = self.kwargs.get('post_id')
        serializer.save(author=self.request.user, post_id=post_id)


class CommentRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    댓글 상세 조회, 수정, 삭제 뷰
    
    GET: 댓글 상세 조회
    PATCH: 댓글 수정
    DELETE: 댓글 삭제
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['get', 'patch', 'delete']  # PUT 제거, PATCH만 허용

    def get_permissions(self):
        """
        HTTP 메서드별 권한 설정
        - GET: 모든 사용자 가능
        - PATCH, DELETE: 로그인한 사용자만 가능
        """
        if self.request.method in ['PATCH', 'DELETE']:
            return [IsAuthenticated()]
        return [IsAuthenticatedOrReadOnly()]

    def get_queryset(self):
        """삭제되지 않은 댓글만 조회"""
        return Comment.objects.filter(is_deleted=False)

    def perform_update(self, serializer):
        """댓글 수정 시 작성자 확인"""
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("댓글을 수정할 권한이 없습니다.")
        serializer.save()

    def perform_destroy(self, instance):
        """댓글 삭제 시 작성자 확인 후 소프트 삭제"""
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("댓글을 삭제할 권한이 없습니다.")
        instance.soft_delete(self.request.user)
