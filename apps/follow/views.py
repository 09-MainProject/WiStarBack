from django.shortcuts import get_object_or_404
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_200_OK,
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.follow.models import Follow
from apps.follow.serializers import FollowSerializer
from apps.idol.models import Idol


class FollowListView(ListAPIView):
    """GET /api/idols/follows - 유저의 아이돌 팔로우 목록 조회"""

    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)


class FollowStatusView(RetrieveAPIView):
    """GET /api/idols/{idol_id}/follow-status - 특정 아이돌 팔로우 여부 확인"""

    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def retrieve(self, request, *args, **kwargs):
        idol_id = self.kwargs.get("idol_id")
        idol = get_object_or_404(Idol, pk=idol_id)
        is_following = Follow.objects.filter(user=request.user, idol=idol).exists()
        return Response({"is_following": is_following}, status=HTTP_200_OK)


class FollowCreateView(CreateAPIView):
    """POST /api/idols/{idol_id}/follows - 아이돌 팔로우 등록"""

    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def create(self, request, *args, **kwargs):
        idol_id = self.kwargs.get("idol_id")
        idol = get_object_or_404(Idol, pk=idol_id)

        if Follow.objects.filter(user=request.user, idol=idol).exists():
            return Response(
                {"detail": "이미 팔로우 중입니다."}, status=HTTP_400_BAD_REQUEST
            )

        follow = Follow.objects.create(user=request.user, idol=idol)
        serializer = self.get_serializer(follow)
        return Response(serializer.data, status=HTTP_201_CREATED)


class FollowDeleteView(DestroyAPIView):
    """DELETE /api/idols/{idol_id}/follows - 아이돌 팔로우 취소"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        idol_id = self.kwargs.get("idol_id")
        idol = get_object_or_404(Idol, pk=idol_id)

        follow = Follow.objects.filter(user=request.user, idol=idol).first()
        if not follow:
            return Response(
                {"detail": "팔로우하지 않았습니다."}, status=HTTP_404_NOT_FOUND
            )

        follow.delete()
        return Response(
            {"detail": "팔로우가 취소되었습니다."}, status=HTTP_204_NO_CONTENT
        )
