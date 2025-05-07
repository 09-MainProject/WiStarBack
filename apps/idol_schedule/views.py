from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Q
from rest_framework import generics, permissions, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Idol, Schedule
from .serializers import ScheduleSerializer


class IsManager(permissions.BasePermission):
    """
    아이돌 매니저(=is_staff=True)만 일정 등록을 할 수 있도록 권한 설정
    """
    def has_permission(self, request, view):
        # 스태프 권한을 가진 사용자만 일정 등록을 할 수 있습니다.
        return request.user and request.user.is_authenticated and request.user.is_staff


class IsIdolManagerOrOwner(permissions.BasePermission):
    """
    아이돌 매니저(스태프 권한을 가진 유저)나 일정 소유자만 일정을 수정하거나 삭제할 수 있도록 허용하는 커스텀 권한
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return request.user in obj.idol.managers.all()  # ✅ ManyToManyField 검사
        return obj.user == request.user  # 본인 소유의 일정인지 확인


class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [IsManager]  # 아이돌 매니저만 일정 생성 가능
    # permission_classes = [AllowAny]  # 포스트맨 테스트용

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

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        return Response(
            {
                "code": 200,
                "message": "일정 목록 조회 성공" if queryset else "일정이 없습니다.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {"code": 201, "message": "일정 등록 성공", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        else:
            print("Serializer Errors:", serializer.errors)
            return Response(
                {"code": 400, "message": "일정 등록에 실패하였습니다.", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )

    # 실제 사용
    def perform_create(self, serializer):
        idol_id = self.kwargs["idol_id"]
        try:
            idol = Idol.objects.get(id=idol_id)
        except ObjectDoesNotExist:
            raise PermissionDenied("해당 아이돌을 찾을 수 없습니다.")

        # 아이돌 담당 매니저 확인
        if idol.user != self.request.user:
            raise PermissionDenied("해당 아이돌에 대한 일정 등록 권한이 없습니다.")

        serializer.save(user=self.request.user, idol=idol)


class ScheduleRetrieveUpdateDeleteView(generics.RetrieveAPIView,
                                       generics.DestroyAPIView,
                                       generics.UpdateAPIView):
    serializer_class = ScheduleSerializer
    permission_classes = [IsIdolManagerOrOwner]

    def get_queryset(self):
        return Schedule.objects.filter(idol_id=self.kwargs["idol_id"])

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(
                {
                    "code": 200,
                    "message": "일정 조회 성공",
                    "data": {"schedule_view": serializer.data},
                },
                status=status.HTTP_200_OK,
            )
        except ObjectDoesNotExist:
            return Response(
                {"code": 404, "message": "일정을 찾을 수 없습니다.", "data": None},
                status=status.HTTP_404_NOT_FOUND,
            )

    def patch(self, request, *args, **kwargs):
        partial = True
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(
                    {"code": 200, "message": "일정 수정 성공", "data": serializer.data},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"code": 400, "message": "일정 수정 실패", "data": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except PermissionDenied:
            return Response(
                {"code": 403, "message": "수정 권한이 없습니다.", "data": None},
                status=status.HTTP_403_FORBIDDEN,
            )

    def delete(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {"code": 204, "message": "일정 삭제 성공", "data": {"schedule_id": instance.id}},
                status=status.HTTP_204_NO_CONTENT,
            )
        except PermissionDenied:
            return Response(
                {"code": 403, "message": "삭제 권한이 없습니다.", "data": None},
                status=status.HTTP_403_FORBIDDEN,
            )

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        instance.delete()
