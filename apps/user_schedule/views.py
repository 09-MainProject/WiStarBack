from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from drf_yasg.utils import swagger_auto_schema

from .models import UserSchedule
from .serializers import UserScheduleSerializer
from utils.responses import user_schedule as R


# 일정 목록 조회 및 생성
class UserScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = UserScheduleSerializer

    def get_queryset(self):
        return UserSchedule.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="내 일정 목록 조회",
        tags=["사용자 일정"],
        responses={200: R.SCHEDULE_LIST_SUCCESS},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {
                "code": R.SCHEDULE_LIST_SUCCESS["code"],
                "message": R.SCHEDULE_LIST_SUCCESS["message"],
                "data": serializer.data,
            },
            status=R.SCHEDULE_LIST_SUCCESS["status"],
        )

    @swagger_auto_schema(
        operation_summary="내 일정 등록",
        tags=["사용자 일정"],
        responses={201: R.SCHEDULE_CREATE_SUCCESS},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # 요청한 사용자 정보를 모델에 직접 할당
        serializer.save(user=request.user)
        return Response(
            {
                "code": R.SCHEDULE_CREATE_SUCCESS["code"],
                "message": R.SCHEDULE_CREATE_SUCCESS["message"],
                "data": serializer.data,
            },
            status=R.SCHEDULE_CREATE_SUCCESS["status"],
        )


# 일정 상세 조회, 수정, 삭제
class UserScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserScheduleSerializer
    queryset = UserSchedule.objects.all()

    def get_object(self):
        try:
            obj = super().get_object()
        except Exception:
            raise NotFound(R.SCHEDULE_NOT_FOUND["message"])

        # 로그인한 사용자의 일정만 접근 가능
        if obj.user != self.request.user:
            raise PermissionDenied(R.SCHEDULE_NO_PERMISSION["message"])

        return obj

    @swagger_auto_schema(
        operation_summary="내 일정 상세 조회",
        tags=["사용자 일정"],
        responses={
            200: R.SCHEDULE_DETAIL_SUCCESS,
            403: R.SCHEDULE_NO_PERMISSION,
            404: R.SCHEDULE_NOT_FOUND,
        },
    )
    def get(self, request, *args, **kwargs):
        schedule = self.get_object()
        serializer = self.get_serializer(schedule)
        return Response(
            {
                "code": R.SCHEDULE_DETAIL_SUCCESS["code"],
                "message": R.SCHEDULE_DETAIL_SUCCESS["message"],
                "data": serializer.data,
            },
            status=R.SCHEDULE_DETAIL_SUCCESS["status"],
        )

    @swagger_auto_schema(
        operation_summary="내 일정 수정",
        tags=["사용자 일정"],
        responses={
            200: R.SCHEDULE_UPDATE_SUCCESS,
            403: R.SCHEDULE_NO_PERMISSION,
            404: R.SCHEDULE_NOT_FOUND,
        },
    )
    def put(self, request, *args, **kwargs):
        schedule = self.get_object()
        serializer = self.get_serializer(schedule, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "code": R.SCHEDULE_UPDATE_SUCCESS["code"],
                "message": R.SCHEDULE_UPDATE_SUCCESS["message"],
                "data": serializer.data,
            },
            status=R.SCHEDULE_UPDATE_SUCCESS["status"],
        )

    @swagger_auto_schema(
        operation_summary="내 일정 삭제",
        tags=["사용자 일정"],
        responses={
            204: R.SCHEDULE_DELETE_SUCCESS,
            403: R.SCHEDULE_NO_PERMISSION,
            404: R.SCHEDULE_NOT_FOUND,
        },
    )
    def delete(self, request, *args, **kwargs):
        schedule = self.get_object()
        schedule.delete()
        return Response(
            {
                "code": R.SCHEDULE_DELETE_SUCCESS["code"],
                "message": R.SCHEDULE_DELETE_SUCCESS["message"],
            },
            status=R.SCHEDULE_DELETE_SUCCESS["status"],
        )