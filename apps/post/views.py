from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import JSONRenderer
from django_filters import rest_framework as filters
from .models import Post
from .serializers import PostSerializer
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action


class PostFilter(filters.FilterSet):
    """게시물 필터"""
    title = filters.CharFilter(lookup_expr='icontains')
    content = filters.CharFilter(lookup_expr='icontains')
    created_at = filters.DateTimeFilter(lookup_expr='gte')
    created_at_end = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

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
    filter_backends = [filters.DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = PostFilter
    ordering_fields = ['created_at', 'views']
    ordering = ['-created_at']
    http_method_names = ['get', 'post', 'patch', 'delete']  # PUT 제거, PATCH만 허용

    def perform_create(self, serializer):
        """게시물 생성 시 작성자 정보 추가"""
        serializer.save(author=self.request.user)

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
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = PostFilter
    ordering_fields = ['created_at', 'views']
    ordering = ['-created_at']

    def get_queryset(self):
        """작성자별 게시물 목록 조회"""
        author_id = self.kwargs.get('author_id')
        return Post.objects.filter(author_id=author_id)
