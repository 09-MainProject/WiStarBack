from rest_framework import generics, status, filters
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import UserSchedule

# Idol 및 팔로우 관련 모델 임포트는 try-except 처리
try:
    from .models import Follow, IdolSchedule
    from .serializers import IdolScheduleSerializer
    IDOL_MODELS_AVAILABLE = True
except ImportError:
    IDOL_MODELS_AVAILABLE = False

from .serializers import UserScheduleSerializer

# django-filter 설치 필요
# 설치 방법:
# pip install django-filter
#
# settings.py에 아래 설정을 추가해야 필터 기능이 정상 작동
# INSTALLED_APPS = ['django_filters', ...]
# REST_FRAMEWORK = {
#     'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
# }


# 사용자 일정 목록 + 생성
class UserScheduleListCreateView(generics.ListCreateAPIView):
    serializer_class = UserScheduleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['title', 'description', 'location', 'start_date', 'end_date']
    search_fields = ['title', 'description', 'location']

    def get_queryset(self):
        return UserSchedule.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        user = request.user

        # ① 사용자 개인 일정
        user_schedules = self.filter_queryset(self.get_queryset())
        user_schedule_data = UserScheduleSerializer(user_schedules, many=True).data

        # ② 사용자가 팔로우한 아이돌 스케줄 (있을 경우만)
        idol_schedule_data = []
        if IDOL_MODELS_AVAILABLE:
            followed_idols = Follow.objects.filter(user=user).values_list('idol', flat=True)
            if followed_idols:
                idol_schedules = IdolSchedule.objects.filter(idol__in=followed_idols)
                idol_schedule_data = IdolScheduleSerializer(idol_schedules, many=True).data

        return Response({
            "code": 200,
            "message": "사용자 + 팔로우 아이돌 일정 목록 조회 성공",
            "data": {
                "user_schedules": user_schedule_data,
                "idol_schedules": idol_schedule_data
            }
        }, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        schedule = serializer.save(user=request.user)
        return Response({
            "code": 201,
            "message": "사용자 일정 등록 성공",
            "data": self.get_serializer(schedule).data
        }, status=status.HTTP_201_CREATED)


# 사용자 일정 단건 조회/수정/삭제
class UserScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserSchedule.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
        except:
            return Response(
                {"code": 400, "message": "일정이 존재하지 않습니다.", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance)
        return Response(
            {
                "code": 200,
                "message": "사용자 일정 조회 성공",
                "data": {"uschedule_view": serializer.data},
            }
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {"code": 400, "message": "수정 권한이 없습니다.", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"code": 200, "message": "일정 수정 성공", "data": serializer.data}
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {"code": 400, "message": "삭제 권한이 없습니다.", "data": None},
                status=status.HTTP_400_BAD_REQUEST,
            )

        schedule_id = instance.id
        self.perform_destroy(instance)
        return Response(
            {
                "code": 204,
                "message": "일정 삭제 성공",
                "data": {"schedule_id": schedule_id},
            },
            status=status.HTTP_204_NO_CONTENT,
        )
