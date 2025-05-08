from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as django_filters
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.contenttypes.models import ContentType
from django.db.models import F
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import Post
from .pagination import PostPagination
from .serializers import PostCreateSerializer, PostSerializer, PostUpdateSerializer
from .utils import process_image
from apps.like.models import Like
from utils.exceptions import CustomAPIException


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
    """
    게시물 CRUD API
    
    게시물의 생성, 조회, 수정, 삭제를 처리합니다.
    """

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
        
        if not self.request.user.is_authenticated:
            message = {
                "create": "게시물을 작성하려면 로그인이 필요합니다.",
                "update": "게시물을 수정하려면 로그인이 필요합니다.",
                "partial_update": "게시물을 수정하려면 로그인이 필요합니다.",
                "destroy": "게시물을 삭제하려면 로그인이 필요합니다.",
                "like": "게시물에 좋아요를 누르려면 로그인이 필요합니다.",
                "unlike": "게시물의 좋아요를 취소하려면 로그인이 필요합니다.",
            }.get(self.action, "로그인이 필요한 서비스입니다.")
            
            raise CustomAPIException({
                "code": 401,
                "message": message,
                "data": None
            })
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

    @swagger_auto_schema(
        operation_summary="게시글 검색",
        operation_description="게시글을 검색합니다.",
        tags=["게시글"],
        responses={
            200: openapi.Response(
                description="게시글 검색 결과입니다.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "게시글 검색 결과입니다.",
                        "data": [
                            {
                                "post_id": 123,
                                "user_id": 42,
                                "title": "5월 앨범 너무 기대돼요!",
                                "content": "5월 앨범 다들 뭐 나오나요? 진짜 최고 기대됨",
                                "thumb_image": "http://example.com/images/five_stage1.jpg",
                                "like_count": 120,
                                "comment_count": 8
                            }
                        ]
                    }
                }
            ),
            400: openapi.Response(
                description="게시글 정보를 찾을 수 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "게시글 정보를 찾을 수 없습니다.",
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
        """게시물 목록을 반환합니다."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="게시글 생성",
        operation_description="게시글을 생성합니다.",
        tags=["게시글"],
        request_body=PostCreateSerializer,
        responses={
            201: openapi.Response(
                description="게시글이 등록되었습니다.",
                examples={
                    "application/json": {
                        "code": 201,
                        "message": "게시글이 등록되었습니다.",
                        "data": {"post_id": 12}
                    }
                }
            ),
            400: openapi.Response(
                description="게시글 작성이 실패하였습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "게시글 작성이 실패하였습니다.",
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
        """게시물을 생성합니다."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # PostSerializer로 응답
        post = serializer.instance
        response_serializer = PostSerializer(post, context={"request": request})
        headers = self.get_success_headers(serializer.data)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @swagger_auto_schema(
        operation_summary="게시글 상세",
        operation_description="게시글 상세 정보를 조회합니다.",
        tags=["게시글"],
        responses={
            200: openapi.Response(
                description="게시글 상세 조회 성공",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "게시글 상세 조회 성공.",
                        "data": {
                            "post_id": 123,
                            "user_id": 42,
                            "title": "5월 앨범 너무 기대돼요!",
                            "content": "5월 앨범 다들 뭐 나오나요? 진짜 최고 기대됨",
                            "thumb_image": "http://example.com/images/five_stage2.jpg",
                            "created_at": "2025-04-23T10:00:00Z",
                            "updated_at": "2025-04-23T10:00:00Z",
                            "like_count": 120,
                            "comment_count": 8,
                            "is_liked": True
                        }
                    }
                }
            ),
            400: openapi.Response(
                description="게시글이 존재하지 않습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "게시글이 존재하지 않습니다.",
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
    def retrieve(self, request, *args, **kwargs):
        """게시물 상세 정보를 반환합니다."""
        post = self.get_object()
        if post.is_deleted:
            return Response({"detail": "삭제된 게시물입니다."}, status=status.HTTP_404_NOT_FOUND)
        # 조회수 증가
        post.views += 1
        post.save(update_fields=["views"])
        serializer = self.get_serializer(post)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="게시글 수정",
        operation_description="게시글을 수정합니다.",
        tags=["게시글"],
        request_body=PostUpdateSerializer,
        responses={
            200: openapi.Response(
                description="게시글이 수정되었습니다.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "게시글이 수정되었습니다.",
                        "data": {"post_id": 12}
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
        """게시물을 수정합니다."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            "code": 200,
            "message": "게시물이 수정되었습니다.",
            "data": {"post_id": instance.id}
        })

    @swagger_auto_schema(
        operation_summary="게시글 부분 수정",
        operation_description="게시글을 부분 수정합니다.",
        tags=["게시글"],
        request_body=PostUpdateSerializer,
        responses={
            200: openapi.Response(
                description="게시글이 수정되었습니다.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "게시글이 수정되었습니다.",
                        "data": {"post_id": 12}
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
        """게시물을 부분 수정합니다."""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="게시글 삭제",
        operation_description="게시글을 삭제합니다.",
        tags=["게시글"],
        responses={
            204: openapi.Response(
                description="게시글이 삭제되었습니다.",
                examples={
                    "application/json": {
                        "code": 204,
                        "message": "게시글이 삭제되었습니다.",
                        "data": {"post_id": 12}
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
        """게시물을 삭제합니다."""
        instance = self.get_object()
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("게시물을 삭제할 권한이 없습니다.")
        instance.soft_delete(self.request.user)
        return Response({
            "code": 204,
            "message": "게시글이 삭제되었습니다.",
            "data": {"post_id": instance.id}
        }, status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="게시글 좋아요",
        operation_description="게시글에 좋아요를 추가합니다.",
        tags=["게시글"],
        responses={
            201: "좋아요 추가 성공",
            400: "이미 좋아요를 누른 게시물",
            401: "인증되지 않은 사용자",
            404: "게시물을 찾을 수 없음"
        }
    )
    @action(detail=True, methods=["post"])
    def like(self, request, pk=None):
        """게시물에 좋아요를 추가합니다."""
        post = self.get_object()
        content_type = ContentType.objects.get_for_model(Post)
        if Like.objects.filter(
            content_type=content_type, object_id=post.id, user=request.user
        ).exists():
            # 이미 좋아요가 있으면 삭제(취소)
            Like.objects.filter(content_type=content_type, object_id=post.id, user=request.user).delete()
            return Response({"status": "unliked"}, status=status.HTTP_200_OK)
        Like.objects.create(
            content_type=content_type, object_id=post.id, user=request.user
        )
        return Response({"status": "liked"}, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="게시글 좋아요 취소",
        operation_description="게시글의 좋아요를 취소합니다.",
        tags=["게시글"],
        responses={
            204: "좋아요 취소 성공",
            401: "인증되지 않은 사용자",
            404: "게시물을 찾을 수 없음"
        }
    )
    @action(detail=True, methods=["post"])
    def unlike(self, request, pk=None):
        """게시물의 좋아요를 취소합니다."""
        post = self.get_object()
        content_type = ContentType.objects.get_for_model(Post)
        Like.objects.filter(
            content_type=content_type, object_id=post.id, user=request.user
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(
        operation_summary="게시글 조회수 증가",
        operation_description="게시글의 조회수를 증가시킵니다.",
        tags=["게시글"],
        responses={
            200: "조회수 증가 성공",
            404: "게시물을 찾을 수 없음"
        }
    )
    @action(detail=True, methods=["post"])
    def increase_views(self, request, pk=None):
        """게시물의 조회수를 증가시킵니다."""
        post = self.get_object()
        post.views = F("views") + 1
        post.save()
        post.refresh_from_db()
        return Response({"views": post.views})


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