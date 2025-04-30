from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from .models import Like
from .serializers import LikeSerializer
from django.shortcuts import get_object_or_404


class LikeViewSet(viewsets.ModelViewSet):
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        type = self.kwargs.get("type")
        object_id = self.kwargs.get("id")
        return Like.objects.filter(type=type, object_id=object_id)

    def create(self, request, *args, **kwargs):
        type = self.kwargs.get("type")
        object_id = self.kwargs.get("id")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def perform_create(self, serializer):
        type = self.kwargs.get("type")
        object_id = self.kwargs.get("id")
        serializer.save(user=self.request.user, type=type, object_id=object_id)

    @action(detail=False, methods=["get"], url_path="like-status")
    def like_status(self, request, type=None, id=None):
        exists = Like.objects.filter(
            type=type, object_id=id, user=request.user
        ).exists()
        return Response({"liked": exists})
