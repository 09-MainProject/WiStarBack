from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, permissions
from rest_framework.response import Response

from utils.responses import idol_schedule as S

from .models import Idol, Schedule
from .serializers import ScheduleSerializer


class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsIdolManagerOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user


class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [IsManager()]  # POST 요청은 매니저만 가능

    def get_queryset(self):
        idol_id = self.kwargs["idol_id"]
        queryset = Schedule.objects.filter(idol_id=idol_id)
        filters = Q()
        params = self.request.query_params

        # 필터 조건 동적 구성
        if title := params.get("title"):
            filters &= Q(title__icontains=title)
        if description := params.get("description"):
            filters &= Q(description__icontains=description)
        if location := params.get("location"):
            filters &= Q(location__icontains=location)
        if start_date := params.get("start_date"):
            filters &= Q(start_date__gte=start_date)
        if end_date := params.get("end_date"):
            filters &= Q(end_date__lte=end_date)

        return queryset.filter(filters)

    @swagger_auto_schema(
        operation_summary="아이돌 스케줄 목록 조회",
        manual_parameters=[
            openapi.Parameter("title", openapi.IN_QUERY, description="제목 검색", type=openapi.TYPE_STRING),
            openapi.Parameter("description", openapi.IN_QUERY, description="설명 검색", type=openapi.TYPE_STRING),
            openapi.Parameter("location", openapi.IN_QUERY, description="장소 검색", type=openapi.TYPE_STRING),
            openapi.Parameter("start_date", openapi.IN_QUERY, description="시작일 이후", type=openapi.FORMAT_DATE),
            openapi.Parameter("end_date", openapi.IN_QUERY, description="종료일 이전", type=openapi.FORMAT_DATE),
        ],
        responses={200: ScheduleSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        message = S.SCHEDULE_LIST_SUCCESS if queryset else S.SCHEDULE_LIST_EMPTY
        return Response(
            {
                "code": message["code"],
                "message": message["message"],
                "data": serializer.data,
            }
        )

    @swagger_auto_schema(
        operation_summary="아이돌 스케줄 등록",
        request_body=ScheduleSerializer,
        responses={201: ScheduleSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {
                    "code": S.SCHEDULE_CREATE_SUCCESS["code"],
                    "message": S.SCHEDULE_CREATE_SUCCESS["message"],
                    "data": serializer.data,
                }
            )
        return Response(
            {
                "code": S.SCHEDULE_CREATE_FAIL["code"],
                "message": S.SCHEDULE_CREATE_FAIL["message"],
                "data": serializer.errors,
            }
        )

    def perform_create(self, serializer):
        idol_id = self.kwargs["idol_id"]
        try:
            idol = Idol.objects.get(id=idol_id)
        except ObjectDoesNotExist:
            # 존재하지 않는 아이돌 ID로 접근 시 예외 처리
            raise PermissionDenied(S.SCHEDULE_IDOL_NOT_FOUND["message"])

        # 아이돌 담당 매니저 여부 검증
        if self.request.user not in idol.managers.all():
            raise PermissionDenied(S.SCHEDULE_PERMISSION_DENIED["message"])

        serializer.save(user=self.request.user, idol=idol)


class ScheduleRetrieveUpdateDeleteView(
    generics.RetrieveAPIView, generics.DestroyAPIView, generics.UpdateAPIView
):
    serializer_class = ScheduleSerializer

    def get_permissions(self):
        # GET은 누구나 접근 가능, 나머지는 관리자 또는 소유자만
        if self.request.method == "GET":
            return [permissions.AllowAny()]  # 인증 없이 접근 허용
        return [IsIdolManagerOrOwner()]  # PATCH, DELETE는 관리자나 소유자만 가능

    def get_queryset(self):
        return Schedule.objects.filter(idol_id=self.kwargs["idol_id"])

    @swagger_auto_schema(
        operation_summary="아이돌 스케줄 상세 조회",
        responses={200: ScheduleSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(
                {
                    "code": S.SCHEDULE_RETRIEVE_SUCCESS["code"],
                    "message": S.SCHEDULE_RETRIEVE_SUCCESS["message"],
                    "data": {"schedule_view": serializer.data},
                }
            )
        except ObjectDoesNotExist:
            return Response(
                {
                    "code": S.SCHEDULE_NOT_FOUND["code"],
                    "message": S.SCHEDULE_NOT_FOUND["message"],
                    "data": None,
                }
            )

    @swagger_auto_schema(
        operation_summary="아이돌 스케줄 수정",
        request_body=ScheduleSerializer,
        responses={200: ScheduleSerializer}
    )
    def patch(self, request, *args, **kwargs):
        partial = True
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(
                    {
                        "code": S.SCHEDULE_UPDATE_SUCCESS["code"],
                        "message": S.SCHEDULE_UPDATE_SUCCESS["message"],
                        "data": serializer.data,
                    }
                )
            return Response(
                {
                    "code": S.SCHEDULE_UPDATE_FAIL["code"],
                    "message": S.SCHEDULE_UPDATE_FAIL["message"],
                    "data": serializer.errors,
                }
            )
        except PermissionDenied:
            return Response(
                {
                    "code": S.SCHEDULE_UPDATE_PERMISSION_DENIED["code"],
                    "message": S.SCHEDULE_UPDATE_PERMISSION_DENIED["message"],
                    "data": None,
                }
            )

    @swagger_auto_schema(
        operation_summary="아이돌 스케줄 삭제",
        responses={204: "삭제 성공"}
    )
    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {
                    "code": S.SCHEDULE_DELETE_SUCCESS["code"],
                    "message": S.SCHEDULE_DELETE_SUCCESS["message"],
                    "data": {"schedule_id": instance.id},
                }
            )
        except PermissionDenied:
            return Response(
                {
                    "code": S.SCHEDULE_DELETE_PERMISSION_DENIED["code"],
                    "message": S.SCHEDULE_DELETE_PERMISSION_DENIED["message"],
                    "data": None,
                }
            )

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()
