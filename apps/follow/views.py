from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    GenericAPIView,
    ListAPIView,
    RetrieveAPIView,
)
from rest_framework.mixins import CreateModelMixin, DestroyModelMixin
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
from utils.responses.follow import FOLLOW_ALREADY_EXISTS, FOLLOW_DELETE_SUCCESS, FOLLOW_NOT_FOUND, \
    FOLLOW_STATUS_SUCCESS, FOLLOW_CREATE_SUCCESS


class FollowListView(ListAPIView):
    """GET /api/idols/follows - 유저의 아이돌 팔로우 목록 조회"""

    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        tags=["아이돌/팔로우"],
        operation_summary="내 팔로우 리스트",
    )
    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class FollowStatusView(RetrieveAPIView):
    """GET /api/idols/{idol_id}/follow-status - 특정 아이돌 팔로우 여부 확인"""

    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["아이돌/팔로우"],
        operation_summary="아이돌 팔로우 여부 확인",
    )
    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        idol_id = self.kwargs.get("idol_id")
        idol = get_object_or_404(Idol, pk=idol_id)
        is_following = Follow.objects.filter(user=request.user, idol=idol).exists()
        return Response(
            {**FOLLOW_STATUS_SUCCESS, "data": {"is_following": is_following}},
            status=FOLLOW_STATUS_SUCCESS["code"]
        )

class FollowCreateDestroyView(GenericAPIView):
    """POST /api/idols/{idol_id}/follows - 아이돌 팔로우 등록 및 취소"""

    serializer_class = FollowSerializer  # 스웨거에서 필요해서 넣음.
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        tags=["아이돌/팔로우"],
        operation_summary="아이돌 팔로우",
    )
    def post(self, request, *args, **kwargs):
        idol_id = self.kwargs.get("idol_id")
        idol = get_object_or_404(Idol, pk=idol_id)

        if Follow.objects.filter(user=request.user, idol=idol).exists():
            return Response(FOLLOW_ALREADY_EXISTS, status=FOLLOW_ALREADY_EXISTS["code"])

        follow = Follow.objects.create(user=request.user, idol=idol)
        serializer = self.get_serializer(follow)
        return Response({**FOLLOW_CREATE_SUCCESS, "data": serializer.data}, status=FOLLOW_CREATE_SUCCESS["code"])

    @swagger_auto_schema(
        tags=["아이돌/팔로우"],
        operation_summary="아이돌 언팔로우",
    )
    def delete(self, request, *args, **kwargs):
        idol_id = self.kwargs.get("idol_id")
        idol = get_object_or_404(Idol, pk=idol_id)

        follow = Follow.objects.filter(user=request.user, idol=idol).first()
        if not follow:
            return Response(FOLLOW_NOT_FOUND, status=FOLLOW_NOT_FOUND["code"])

        follow.delete()
        return Response(FOLLOW_DELETE_SUCCESS, status=FOLLOW_DELETE_SUCCESS["code"])
