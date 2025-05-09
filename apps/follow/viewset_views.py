# apps/follow/views.py
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.follow.models import Follow
from apps.follow.serializers import FollowSerializer
from apps.idol.models import Idol


class FollowViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @action(detail=True, methods=["post"])
    def follow(self, request, pk=None):
        idol = get_object_or_404(Idol, pk=pk)
        user = request.user

        # 중복 팔로우 방지
        if Follow.objects.filter(user=user, idol=idol).exists():
            return Response(
                {"detail": "이미 팔로우했습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        follow = Follow.objects.create(user=user, idol=idol)
        serializer = FollowSerializer(follow)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"])
    def unfollow(self, request, pk=None):
        idol = get_object_or_404(Idol, pk=pk)
        user = request.user

        follow = Follow.objects.filter(user=user, idol=idol).first()
        if not follow:
            return Response(
                {"detail": "팔로우하지 않았습니다."}, status=status.HTTP_400_BAD_REQUEST
            )

        follow.delete()
        return Response({"detail": "언팔로우 완료"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"])
    def followers(self, request, pk=None):
        idol = get_object_or_404(Idol, pk=pk)
        followers = Follow.objects.filter(idol=idol)
        serializer = FollowSerializer(followers, many=True)
        return Response(serializer.data)
