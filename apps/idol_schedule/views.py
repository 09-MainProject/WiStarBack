from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from rest_framework import generics, permissions
from rest_framework.response import Response

from .models import Idol, Schedule
from .serializers import ScheduleSerializer
from utils.responses import idol_schedule as S  # 응답 메시지 분리


# 매니저 권한을 가진 사용자만 접근 가능
class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_staff


# 아이돌 소유자이거나 관리자일 경우에만 수정/삭제 가능
class IsIdolManagerOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return request.user in obj.idol.managers.all()
        return obj.user == request.user


class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer

    # 요청 메서드에 따라 권한 분기: GET은 전체 공개, POST는 매니저만 가능
    def get_permissions(self):
        if self.request.method == "GET":
            return [permissions.AllowAny()]
        return [IsManager()]

    # 필터링 및 검색 기능 포함
    def get_queryset(self):
        idol_id = self.kwargs["idol_id"]
        queryset = Schedule.objects.filter(idol_id=idol_id)
        filters = Q()
        params = self.request.query_params

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

    # 일정 목록 조회
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        message = S.SCHEDULE_LIST_SUCCESS if queryset else S.SCHEDULE_LIST_EMPTY
        return Response(
            {"code": message["code"], "message": message["message"], "data": serializer.data}
        )

    # 일정 등록
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

    # 아이돌 유효성 및 권한 검증
    def perform_create(self, serializer):
        idol_id = self.kwargs["idol_id"]
        try:
            idol = Idol.objects.get(id=idol_id)
        except ObjectDoesNotExist:
            raise PermissionDenied(S.SCHEDULE_IDOL_NOT_FOUND["message"])

        if self.request.user not in idol.managers.all():
            raise PermissionDenied(S.SCHEDULE_PERMISSION_DENIED["message"])

        serializer.save(user=self.request.user, idol=idol)


class ScheduleRetrieveUpdateDeleteView(generics.RetrieveAPIView,
                                       generics.DestroyAPIView,
                                       generics.UpdateAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [IsIdolManagerOrOwner]

    def get_queryset(self):
        return Schedule.objects.filter(idol_id=self.kwargs["idol_id"])

    # 일정 상세 조회
    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(
                {"code": S.SCHEDULE_RETRIEVE_SUCCESS["code"], "message": S.SCHEDULE_RETRIEVE_SUCCESS["message"], "data": {"schedule_view": serializer.data}}
            )
        except ObjectDoesNotExist:
            return Response(
                {"code": S.SCHEDULE_NOT_FOUND["code"], "message": S.SCHEDULE_NOT_FOUND["message"], "data": None}
            )

    # 일정 수정
    def patch(self, request, *args, **kwargs):
        partial = True
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(
                    {"code": S.SCHEDULE_UPDATE_SUCCESS["code"], "message": S.SCHEDULE_UPDATE_SUCCESS["message"], "data": serializer.data}
                )
            return Response(
                {"code": S.SCHEDULE_UPDATE_FAIL["code"], "message": S.SCHEDULE_UPDATE_FAIL["message"], "data": serializer.errors}
            )
        except PermissionDenied:
            return Response(
                {"code": S.SCHEDULE_UPDATE_PERMISSION_DENIED["code"], "message": S.SCHEDULE_UPDATE_PERMISSION_DENIED["message"], "data": None}
            )

    # 일정 삭제
    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {"code": S.SCHEDULE_DELETE_SUCCESS["code"], "message": S.SCHEDULE_DELETE_SUCCESS["message"], "data": {"schedule_id": instance.id}}
            )
        except PermissionDenied:
            return Response(
                {"code": S.SCHEDULE_DELETE_PERMISSION_DENIED["code"], "message": S.SCHEDULE_DELETE_PERMISSION_DENIED["message"], "data": None}
            )

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()