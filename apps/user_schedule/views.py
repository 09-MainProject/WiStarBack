from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import UserSchedule
from .serializers import UserScheduleSerializer

# Idol 관련 모듈은 선택적 import
try:
    from .models import Follow, IdolSchedule
    from .serializers import IdolScheduleSerializer
    IDOL_MODELS_AVAILABLE = True
except ImportError:
    IDOL_MODELS_AVAILABLE = False

from utils.responses.user_schedule import (
    SCHEDULE_LIST_SUCCESS,
    SCHEDULE_CREATE_SUCCESS,
    SCHEDULE_DETAIL_SUCCESS,
    SCHEDULE_UPDATE_SUCCESS,
    SCHEDULE_DELETE_SUCCESS,
    SCHEDULE_ERROR_RESPONSE,
)


class UserScheduleBaseView:
    serializer_class = UserScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSchedule.objects.filter(user=self.request.user)


class UserScheduleListCreateView(UserScheduleBaseView, generics.ListCreateAPIView):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['title', 'description', 'location', 'start_date', 'end_date']
    search_fields = ['title', 'description', 'location']

    @swagger_auto_schema(
        operation_summary="내 일정 + 팔로우 아이돌 일정 통합 조회",
        tags=["사용자 일정 / 목록"],
        manual_parameters=[
            openapi.Parameter(
                name="Authorization",
                in_=openapi.IN_HEADER,
                type=openapi.TYPE_STRING,
                description="Bearer 액세스 토큰",
                required=True,
                example="Bearer <access_token>",
            ),
            openapi.Parameter(
                name="title",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="일정 제목 필터",
                required=False,
            ),
            openapi.Parameter(
                name="start_date",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                format="date",
                description="시작일 필터 (예: 2025-05-01)",
                required=False,
            ),
        ],
        responses={
            200: SCHEDULE_LIST_SUCCESS,
            401: openapi.Response(
                description="JWT 인증 실패",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "code": openapi.Schema(type=openapi.TYPE_INTEGER, example=401),
                        "message": openapi.Schema(type=openapi.TYPE_STRING, example="인증 정보가 없습니다."),
                        "data": openapi.Schema(type=openapi.TYPE_OBJECT, nullable=True),
                    },
                ),
            ),
        }
    )
    def list(self, request, *args, **kwargs):
        user = request.user
        user_schedules = self.filter_queryset(self.get_queryset())
        user_schedule_data = self.get_serializer(user_schedules, many=True).data

        idol_schedule_data = []
        if IDOL_MODELS_AVAILABLE:
            followed_idols = Follow.objects.filter(user=user).values_list('idol', flat=True)
            idol_schedules = IdolSchedule.objects.filter(idol__in=followed_idols)
            idol_schedule_data = IdolScheduleSerializer(idol_schedules, many=True).data

        return Response({
            "code": 200,
            "message": "사용자 + 팔로우 아이돌 일정 목록 조회 성공",
            "data": {
                "user_schedules": user_schedule_data,
                "idol_schedules": idol_schedule_data
            }
        })

    @swagger_auto_schema(
        operation_summary="내 일정 등록",
        tags=["사용자 일정 / 생성"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["title", "start_date", "end_date"],
            properties={
                "title": openapi.Schema(type=openapi.TYPE_STRING, example="치과 예약"),
                "description": openapi.Schema(type=openapi.TYPE_STRING, example="강남역 치과 방문"),
                "location": openapi.Schema(type=openapi.TYPE_STRING, example="강남구 강남대로 123"),
                "start_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-05-09"),
                "end_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-05-09"),
            },
        ),
        responses={201: SCHEDULE_CREATE_SUCCESS}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save(user=request.user)

        return Response({
            "code": 201,
            "message": "사용자 일정 등록 성공",
            "data": self.get_serializer(schedule).data
        }, status=status.HTTP_201_CREATED)


class UserScheduleDetailView(UserScheduleBaseView, generics.RetrieveUpdateDestroyAPIView):

    def _check_ownership(self, instance, request):
        if instance.user != request.user:
            return Response(
                {"code": 400, "message": "권한이 없습니다.", "data": None},
                status=status.HTTP_400_BAD_REQUEST
            )
        return None

    @swagger_auto_schema(
        operation_summary="내 일정 상세 조회",
        tags=["사용자 일정 / 단건 조회"],
        responses={
            200: SCHEDULE_DETAIL_SUCCESS,
            400: SCHEDULE_ERROR_RESPONSE,
        }
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except:
            return Response(
                {"code": 400, "message": "일정이 존재하지 않습니다.", "data": None},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = self.get_serializer(instance).data
        return Response({
            "code": 200,
            "message": "사용자 일정 조회 성공",
            "data": {"uschedule_view": data}
        })

    @swagger_auto_schema(
        operation_summary="내 일정 수정",
        tags=["사용자 일정 / 수정"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "title": openapi.Schema(type=openapi.TYPE_STRING, example="수정된 일정 제목"),
                "description": openapi.Schema(type=openapi.TYPE_STRING, example="수정된 설명"),
                "location": openapi.Schema(type=openapi.TYPE_STRING, example="수정된 장소"),
                "start_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-05-10"),
                "end_date": openapi.Schema(type=openapi.TYPE_STRING, format="date", example="2025-05-10"),
            },
        ),
        responses={
            200: SCHEDULE_UPDATE_SUCCESS,
            400: SCHEDULE_ERROR_RESPONSE,
        }
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        permission_error = self._check_ownership(instance, request)
        if permission_error:
            return permission_error

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response({
            "code": 200,
            "message": "일정 수정 성공",
            "data": serializer.data
        })

    @swagger_auto_schema(
        operation_summary="내 일정 삭제",
        tags=["사용자 일정 / 삭제"],
        responses={
            204: SCHEDULE_DELETE_SUCCESS,
            400: SCHEDULE_ERROR_RESPONSE,
        }
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        permission_error = self._check_ownership(instance, request)
        if permission_error:
            return permission_error

        schedule_id = instance.id
        self.perform_destroy(instance)

        return Response({
            "code": 204,
            "message": "일정 삭제 성공",
            "data": {"schedule_id": schedule_id}
        }, status=status.HTTP_204_NO_CONTENT)
