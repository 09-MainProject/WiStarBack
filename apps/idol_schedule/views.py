from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from rest_framework import generics, permissions, status
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
        # 사용자가 아이돌 매니저(스태프)인지 확인
        if request.user.is_staff:
            # 아이돌 매니저라면 해당 아이돌의 일정 수정/삭제 가능
            return obj.idol.user == request.user
        # 사용자가 스케줄 소유자인지 확인 (본인 일정을 수정/삭제 가능)
        return obj.user == request.user

    def has_permission(self, request, view):
        idol_id = view.kwargs.get("idol_id")
        idol = Idol.objects.get(id=idol_id)
        if request.user.is_authenticated and request.user.userprofile.is_manager:
            # 관리자가 담당하는 아이돌인지 확인
            if idol in request.user.userprofile.managed_idols.all():
                return True
        return False

class ScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = ScheduleSerializer
    # permission_classes = [IsManager]  # 아이돌 매니저만 일정 생성 가능

    permission_classes = [AllowAny] # 포스트맨 테스트용

    def get_queryset(self):
        idol_id = self.kwargs["idol_id"]
        queryset = Schedule.objects.filter(idol_id=idol_id)

        # 필터링을 위한 쿼리 파라미터 가져오기
        filters = Q()

        title = self.request.query_params.get("title")
        description = self.request.query_params.get("description")
        location = self.request.query_params.get("location")
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")

        if title:
            filters &= Q(title__icontains=title)
        if description:
            filters &= Q(description__icontains=description)
        if location:
            filters &= Q(location__icontains=location)
        if start_date:
            filters &= Q(start_date__gte=start_date)
        if end_date:
            filters &= Q(end_date__lte=end_date)

        # 필터 조건을 적용하여 쿼리셋 반환
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
        serializer.save(user=self.request.user, idol=idol)

    # 테스트용
    # def perform_create(self, serializer):
    #     idol_id = self.kwargs["idol_id"]  # URL에서 아이돌 ID 받기
    #     idol = Idol.objects.get(id=idol_id)  # 아이돌 객체 찾기
    #     user = self.request.user if self.request.user.is_authenticated else None
    #     # idol 필드를 serializer에 자동으로 추가하여 저장
    #     serializer.save(user=user, idol=idol)  # serializer에 user와 idol 추가하여 저장


class ScheduleRetrieveUpdateDeleteView(
    generics.RetrieveAPIView, generics.DestroyAPIView
):
    serializer_class = ScheduleSerializer
    permission_classes = [IsIdolManagerOrOwner]  # 커스텀 권한 추가

    def get_queryset(self):
        # 특정 아이돌의 일정만 조회할 수 있도록 필터링
        return Schedule.objects.filter(idol_id=self.kwargs["idol_id"])

    def retrieve(self, request, *args, **kwargs):
        # 일정을 조회하는 로직 (GET 요청)
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
        """
        일정 수정 (PATCH 요청)
        """
        partial = True  # 수정은 부분 업데이트로 처리
        try:
            instance = self.get_object()
            serializer = self.get_serializer(
                instance, data=request.data, partial=partial
            )
            if serializer.is_valid():
                self.perform_update(serializer)
                return Response(
                    {"code": 200, "message": "일정 수정 성공", "data": serializer.data},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "code": 400,
                        "message": "일정 수정에 실패하였습니다.",
                        "data": None,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except PermissionDenied:
            return Response(
                {"code": 403, "message": "수정 권한이 없습니다.", "data": None},
                status=status.HTTP_403_FORBIDDEN,
            )

    def delete(self, request, *args, **kwargs):
        """
        일정 삭제 (DELETE 요청)
        """
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response(
                {
                    "code": 204,
                    "message": "일정 삭제 성공",
                    "data": {"schedule_id": instance.id},
                },
                status=status.HTTP_204_NO_CONTENT,
            )
        except PermissionDenied:
            return Response(
                {"code": 403, "message": "삭제 권한이 없습니다.", "data": None},
                status=status.HTTP_403_FORBIDDEN,
            )

    def perform_update(self, serializer):
        """
        수정된 데이터를 저장하는 메소드
        """
        # 실제 객체를 저장하는 로직
        serializer.save()  # 여기에 추가적인 로직을 넣을 수 있음 (예: 사용자 업데이트)

    def perform_destroy(self, instance):
        """
        일정 삭제 메소드
        """
        instance.delete()  # 실제 객체를 삭제하는 로직