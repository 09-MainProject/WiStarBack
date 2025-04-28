from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.renderers import JSONRenderer
from django_filters import rest_framework as filters
from .models import Post
from .serializers import PostSerializer


class PostFilter(filters.FilterSet):
    """게시물 필터"""
    title = filters.CharFilter(lookup_expr='icontains')
    content = filters.CharFilter(lookup_expr='icontains')
    created_at = filters.DateTimeFilter(lookup_expr='gte')
    created_at_end = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Post
        fields = ['title', 'content', 'created_at', 'created_at_end', 'author']


class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = PostFilter
    ordering_fields = ['created_at', 'views']
    ordering = ['-created_at']
    renderer_classes = [JSONRenderer]

    def perform_create(self, serializer):
        """게시물 생성 시 작성자 정보 추가"""
        serializer.save(author=self.request.user)


class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    게시물 상세 조회, 수정, 삭제 뷰

    GET: 게시물 상세 조회
    PUT: 게시물 수정
    DELETE: 게시물 삭제
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        """게시물 수정 시 작성자 확인"""
        if serializer.instance.author != self.request.user:
            return Response(
                {"detail": "게시물을 수정할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer.save()

    def perform_destroy(self, instance):
        """게시물 삭제 시 작성자 확인"""
        if instance.author != self.request.user:
            return Response(
                {"detail": "게시물을 삭제할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()


class PostIncreaseViewsView(generics.UpdateAPIView):
    """
    게시물 조회수 증가 뷰

    POST: 게시물 조회수 증가
    """
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
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
