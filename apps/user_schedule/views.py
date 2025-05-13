from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response

from utils.responses import user_schedule as R
from .models import UserSchedule
from .serializers import UserScheduleSerializer


# 일정 목록 조회 및 생성
class UserScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = UserScheduleSerializer

    def get_queryset(self):
        return UserSchedule.objects.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_summary="내 일정 목록 조회",
        tags=["사용자 일정"],
        responses={
            200: UserScheduleSerializer(many=True),  # ✅ 수정됨
        }
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
        request_body=UserScheduleSerializer,  # ✅ 추가됨
        responses={
            201: UserScheduleSerializer(),  # ✅ 수정됨
        }
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
    http_method_names = ["get", "patch", "delete"]
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
            200: UserScheduleSerializer(),  # ✅ 수정됨
            403: "접근 권한이 없습니다.",
            404: "일정을 찾을 수 없습니다.",
        }
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
        request_body=UserScheduleSerializer,  # ✅ 추가됨
        responses={
            200: UserScheduleSerializer(),  # ✅ 수정됨
            403: "접근 권한이 없습니다.",
            404: "일정을 찾을 수 없습니다.",
        }
    )
    def patch(self, request, *args, **kwargs):  # ✅ put → patch
        schedule = self.get_object()
        serializer = self.get_serializer(schedule, data=request.data, partial=True)  # ✅ partial=True
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
            204: "일정 삭제 성공",  # ✅ 설명만 넣음 (직렬화 필요 없음)
            403: "접근 권한이 없습니다.",
            404: "일정을 찾을 수 없습니다.",
        }
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