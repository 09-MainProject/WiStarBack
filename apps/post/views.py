import logging

from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import F
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as django_filters
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.like.models import Like
from utils.exceptions import CustomAPIException

from .models import Post
from .pagination import PostPagination
from .serializers import PostCreateSerializer, PostSerializer, PostUpdateSerializer
from .utils import process_image

logger = logging.getLogger(__name__)


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

    http_method_names = ["get", "post", "patch", "delete"]
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
    authentication_classes = [JWTAuthentication]

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
                "likes": "게시물에 좋아요를 누르려면 로그인이 필요합니다.",
                "unlikes": "게시물의 좋아요를 취소하려면 로그인이 필요합니다.",
            }.get(self.action, "로그인이 필요한 서비스입니다.")

            raise CustomAPIException({"code": 401, "message": message, "data": None})
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
            post = serializer.save(author=self.request.user)
            image_file = self.request.FILES.get("image")
            if image_file:
                # Cloudinary 업로드 방식
                # from utils.CloudinaryImageMixin import upload_to_cloudinary
                #
                # image_url, public_id = upload_to_cloudinary(image_file, folder="posts")
                # post.image_url = image_url
                # post.image_public_id = public_id
                post.save()
        except ValidationError as e:
            logger.error(f"게시글 생성 중 유효성 검사 오류: {e}")
            raise CustomAPIException({"code": 400, "message": str(e), "data": None})
        except Exception as e:
            logger.error(f"게시글 생성 중 오류 발생: {e}")
            raise CustomAPIException(
                {
                    "code": 500,
                    "message": "게시글 생성 중 오류가 발생했습니다.",
                    "data": None,
                }
            )

    def perform_update(self, serializer):
        """게시물을 수정합니다."""
        post = self.get_object()
        if post.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("게시물을 수정할 권한이 없습니다.")

        image_file = self.request.FILES.get("image")
        if image_file:
            # Cloudinary 업로드 방식
            # from utils.CloudinaryImageMixin import upload_to_cloudinary
            #
            # image_url, public_id = upload_to_cloudinary(image_file, folder="posts")
            # serializer.save(image_url=image_url, image_public_id=public_id)
            serializer.save()
        else:
            serializer.save()

    def perform_destroy(self, instance):
        """게시물을 소프트 삭제합니다."""
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("게시물을 삭제할 권한이 없습니다.")
        instance.soft_delete(self.request.user)

    @swagger_auto_schema(
        operation_summary="게시글 목록 조회",
        operation_description="게시글 전체 목록을 조회합니다. (필터 및 검색 가능)",
        tags=["posts"],
        responses={
            200: openapi.Response(
                description="게시글 목록 조회 결과입니다.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "게시글 목록 조회 결과입니다.",
                        "data": [
                            {
                                "id": 123,
                                "author": "nickname",
                                "title": "아이브 컴백 너무 기대돼요!",
                                "content": "5월 컴백 무대 다들 봤나요? 진짜 최고였어요 🥹",
                                "image": "image_file.jpg",
                                "image_url": "http://example.com/images/ive_stage1.jpg",
                                "created_at": "2025-04-23T10:00:00Z",
                                "updated_at": "2025-04-23T10:00:00Z",
                                "views": 100,
                                "likes_count": 120,
                                "is_liked": True,
                                "is_deleted": False,
                            }
                        ],
                    }
                },
            ),
            400: openapi.Response(
                description="게시글 정보를 찾을 수 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "게시글 정보를 찾을 수 없습니다.",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None,
                    }
                },
            ),
        },
    )
    def list(self, request, *args, **kwargs):
        """게시물 목록을 반환합니다."""
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="게시글 검색",
        operation_description="키워드로 게시글을 검색합니다.",
        tags=["posts"],
        manual_parameters=[
            openapi.Parameter(
                "q",
                openapi.IN_QUERY,
                description="검색어 (제목/내용)",
                type=openapi.TYPE_STRING,
            ),
        ],
        responses={
            200: openapi.Response(
                description="게시글 검색 결과입니다.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "게시글 검색 결과입니다.",
                        "data": [
                            {
                                "id": 123,
                                "author": "nickname",
                                "title": "아이브 컴백 너무 기대돼요!",
                                "content": "5월 컴백 무대 다들 봤나요? 진짜 최고였어요 🥹",
                                "image": "image_file.jpg",
                                "image_url": "http://example.com/images/ive_stage1.jpg",
                                "created_at": "2025-04-23T10:00:00Z",
                                "updated_at": "2025-04-23T10:00:00Z",
                                "views": 100,
                                "likes_count": 120,
                                "is_liked": True,
                                "is_deleted": False,
                            }
                        ],
                    }
                },
            ),
            400: openapi.Response(
                description="게시글 정보를 찾을 수 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "게시글 정보를 찾을 수 없습니다.",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None,
                    }
                },
            ),
        },
    )
    @action(detail=False, methods=["get"], url_path="search", name="search")
    def posts_search(self, request):
        q = request.query_params.get("q", "")
        queryset = Post.objects.filter(is_deleted=False)
        if q:
            queryset = queryset.filter(title__icontains=q)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = PostSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="게시글 생성",
        operation_description="새로운 게시글을 생성합니다.",
        tags=["posts"],
        request_body=PostCreateSerializer,
        responses={
            201: openapi.Response(
                description="게시글이 성공적으로 생성되었습니다.",
                examples={
                    "application/json": {
                        "code": 201,
                        "message": "게시글이 성공적으로 생성되었습니다.",
                        "data": {
                            "id": 123,
                            "author": "nickname",
                            "title": "아이브 컴백 너무 기대돼요!",
                            "content": "5월 컴백 무대 다들 봤나요? 진짜 최고였어요 🥹",
                            "image": "image_file.jpg",
                            "image_url": "http://example.com/images/ive_stage1.jpg",
                            "created_at": "2025-04-23T10:00:00Z",
                            "updated_at": "2025-04-23T10:00:00Z",
                            "views": 100,
                            "likes_count": 120,
                            "is_liked": True,
                            "is_deleted": False,
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="게시글 생성 중 유효성 검사 오류",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "게시글 생성 중 유효성 검사 오류",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None,
                    }
                },
            ),
        },
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
        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    @swagger_auto_schema(
        operation_summary="게시글 상세 조회",
        operation_description="게시글의 상세 정보를 조회합니다.",
        tags=["posts"],
        responses={
            200: openapi.Response(
                description="게시글 상세 조회 성공",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "게시글 상세 조회 성공",
                        "data": {
                            "id": 123,
                            "author": "nickname",
                            "title": "아이브 컴백 너무 기대돼요!",
                            "content": "5월 컴백 무대 다들 봤나요? 진짜 최고였어요 🥹",
                            "image": "image_file.jpg",
                            "image_url": "http://example.com/images/ive_stage1.jpg",
                            "created_at": "2025-04-23T10:00:00Z",
                            "updated_at": "2025-04-23T10:00:00Z",
                            "views": 100,
                            "likes_count": 120,
                            "is_liked": True,
                            "is_deleted": False,
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="게시글이 존재하지 않습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "게시글이 존재하지 않습니다.",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None,
                    }
                },
            ),
        },
    )
    def retrieve(self, request, *args, **kwargs):
        """게시물을 반환합니다."""
        try:
            instance = self.get_object()
            # 삭제된 게시물인지 확인
            if instance.is_deleted:
                return Response(
                    {
                        "code": 404,
                        "message": "게시물을 찾을 수 없습니다.",
                        "data": None,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # 해당 게시물을 보는 사용자가 인증된 사용자인지 확인
            if request.user.is_authenticated:
                instance.views = F("views") + 1
                instance.save(update_fields=["views"])
                instance.refresh_from_db()

            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {
                    "code": 500,
                    "message": "서버 내부 오류가 발생했습니다.",
                    "data": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        operation_summary="게시글 부분 수정",
        operation_description="게시글의 일부 정보를 수정합니다.",
        tags=["posts"],
        request_body=PostUpdateSerializer,
        responses={
            200: openapi.Response(
                description="게시글이 수정되었습니다.",
                examples={
                    "application/json": {
                        "code": 200,
                        "message": "게시글이 수정되었습니다.",
                        "data": {
                            "id": 123,
                            "author": "nickname",
                            "title": "아이브 컴백 너무 기대돼요!",
                            "content": "5월 컴백 무대 다들 봤나요? 진짜 최고였어요 🥹",
                            "image": "image_file.jpg",
                            "image_url": "http://example.com/images/ive_stage1.jpg",
                            "created_at": "2025-04-23T10:00:00Z",
                            "updated_at": "2025-04-23T10:00:00Z",
                            "views": 100,
                            "likes_count": 120,
                            "is_liked": True,
                            "is_deleted": False,
                        },
                    }
                },
            ),
            400: openapi.Response(
                description="수정 권한이 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "수정 권한이 없습니다.",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None,
                    }
                },
            ),
        },
    )
    def partial_update(self, request, *args, **kwargs):
        """게시물을 부분 수정합니다."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="게시글 삭제",
        operation_description="게시글을 삭제합니다.",
        tags=["posts"],
        responses={
            204: openapi.Response(
                description="게시글이 삭제되었습니다.",
                examples={
                    "application/json": {
                        "code": 204,
                        "message": "게시글이 삭제되었습니다.",
                        "data": None,
                    }
                },
            ),
            400: openapi.Response(
                description="삭제 권한이 없습니다.",
                examples={
                    "application/json": {
                        "code": 400,
                        "message": "삭제 권한이 없습니다.",
                        "data": None,
                    }
                },
            ),
            500: openapi.Response(
                description="서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                examples={
                    "application/json": {
                        "code": 500,
                        "message": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요.",
                        "data": None,
                    }
                },
            ),
        },
    )
    def destroy(self, request, *args, **kwargs):
        """게시물을 삭제합니다."""
        instance = self.get_object()
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied("게시물을 삭제할 권한이 없습니다.")
        instance.soft_delete(self.request.user)
        return Response(
            {
                "code": 204,
                "message": "게시글이 삭제되었습니다.",
                "data": {"post_id": instance.id},
            },
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(detail=True, methods=["post", "delete"], url_path="likes")
    def likes(self, request, pk=None):
        """게시글 좋아요/취소 API (POST: 좋아요, DELETE: 좋아요 취소)"""
        post = self.get_object()
        user = request.user
        if request.method == "POST":
            # 이미 좋아요가 있으면 아무 변화 없음
            like, created = Like.objects.get_or_create(post=post, user=user)
            return Response(
                {"status": "liked"},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
            )
        elif request.method == "DELETE":
            deleted, _ = Like.objects.filter(post=post, user=user).delete()
            return Response(
                {"status": "unliked"},
                status=status.HTTP_204_NO_CONTENT if deleted else status.HTTP_200_OK,
            )
