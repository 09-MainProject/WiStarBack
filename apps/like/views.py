from django.contrib.contenttypes.models import ContentType
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Like
from .serializers import LikeSerializer


class LikeViewSet(viewsets.ModelViewSet):
    """좋아요 뷰셋"""

    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """좋아요 목록을 반환합니다."""
        # Swagger 문서 생성 중일 경우 빈 쿼리셋 반환
        if getattr(self, 'swagger_fake_view', False):
            return Like.objects.none()

        content_type = ContentType.objects.get(
            app_label=self.kwargs.get("app_label"),
            model=self.kwargs.get("model"),
        )
        object_id = self.kwargs.get("object_id")
        return Like.objects.filter(content_type=content_type, object_id=object_id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        """좋아요를 생성합니다."""
        content_type = ContentType.objects.get(
            app_label=self.kwargs.get("app_label"),
            model=self.kwargs.get("model"),
        )
        object_id = self.kwargs.get("object_id")
        serializer.save(
            user=self.request.user, content_type=content_type, object_id=object_id
        )

    @action(detail=False, methods=["get"])
    def like_status(self, request, app_label=None, model=None, object_id=None):
        """좋아요 상태를 반환합니다."""
        content_type = ContentType.objects.get(app_label=app_label, model=model)
        exists = Like.objects.filter(
            content_type=content_type, object_id=object_id, user=request.user
        ).exists()
        return Response({"liked": exists})

    def destroy(self, request, *args, **kwargs):
        """좋아요를 삭제합니다."""
        instance = self.get_object()
        if instance.user != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)
