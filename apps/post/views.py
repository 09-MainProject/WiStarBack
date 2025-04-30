from django.core.exceptions import PermissionDenied
from django_filters import rest_framework as django_filters
from rest_framework import filters, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Post
from .pagination import PostPagination
from .serializers import PostCreateSerializer, PostSerializer, PostUpdateSerializer
from .utils import process_image


class PostFilter(django_filters.FilterSet):
    """게시글 필터"""

    title = django_filters.CharFilter(lookup_expr="icontains")
    content = django_filters.CharFilter(lookup_expr="icontains")
    created_at = django_filters.DateTimeFilter(lookup_expr="gte")
    created_at_end = django_filters.DateTimeFilter(
        field_name="created_at", lookup_expr="lte"
    )

    class Meta:
        model = Post
        fields = ["title", "content", "created_at", "created_at_end"]


class PostViewSet(viewsets.ModelViewSet):
    """게시물 뷰셋"""

    filter_backends = [
        django_filters.DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_class = PostFilter
    search_fields = ["title", "content"]
    ordering_fields = ["created_at", "views"]
    ordering = ["-created_at"]
    pagination_class = PostPagination
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        """
        액션에 따라 권한을 설정합니다.
        - 조회(GET): 모든 사용자 가능
        - 생성(POST), 수정(PATCH), 삭제(DELETE): 인증된 사용자만 가능
        """
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        """게시물 목록을 반환합니다."""
        if self.action == "retrieve":
            queryset = Post.objects.all()
        else:
            queryset = Post.objects.filter(is_deleted=False)

        if self.action == "list":
            # 필터링, 검색, 정렬 적용
            for backend in list(self.filter_backends):
                queryset = backend().filter_queryset(self.request, queryset, self)
        return queryset

    def get_serializer_class(self):
        """액션에 따라 적절한 시리얼라이저를 반환합니다."""
        if self.action == "create":
            return PostCreateSerializer
        elif self.action in ["update", "partial_update"]:
            return PostUpdateSerializer
        return PostSerializer

    def perform_create(self, serializer):
        """게시물을 생성합니다."""
        try:
            # 이미지 처리
            if "image" in self.request.FILES:
                image_file = self.request.FILES["image"]
                processed_image = process_image(image_file)
                serializer.save(author=self.request.user, image=processed_image)
            else:
                serializer.save(author=self.request.user)
        except Exception as e:
            print(f"이미지 처리 중 오류 발생: {e}")
            raise

    def perform_update(self, serializer):
        """게시물을 수정합니다."""
        post = self.get_object()
        if post.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("게시물을 수정할 권한이 없습니다.")

        # 이미지 처리
        if "image" in self.request.FILES:
            image_file = self.request.FILES["image"]
            processed_image = process_image(image_file)
            serializer.save(image=processed_image)
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """게시물을 소프트 삭제합니다."""
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("게시물을 삭제할 권한이 없습니다.")
        instance.soft_delete(self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """게시물을 조회하고 조회수를 증가시킵니다."""
        instance = self.get_object()
        if instance.is_deleted:
            return Response(status=status.HTTP_404_NOT_FOUND)
        instance.views += 1
        instance.save(update_fields=["views"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def restore(self, request, pk=None):
        """삭제된 게시물을 복구합니다."""
        post = self.get_object()
        if post.author != request.user and not request.user.is_staff:
            raise PermissionDenied("게시물을 복구할 권한이 없습니다.")
        post.restore()
        return Response(PostSerializer(post).data)


class PostLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None):
        post = get_object_or_404(Post, pk=pk)
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
            return Response({"status": "unliked"})
        else:
            post.likes.add(request.user)
            return Response({"status": "liked"})
