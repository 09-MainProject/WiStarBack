from django_filters import rest_framework as dj_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions
from rest_framework.decorators import action

# , ScheduleSerializer
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.idol.models import Idol

# , Schedule
from apps.idol.serializers import IdolSerializer


class IdolFilter(dj_filters.FilterSet):
    """
    아이돌 검색 필터

    Attributes:
        name (str): 아이돌 이름 (부분 일치)
        agency (str): 소속사 (부분 일치)
        debut_date (date): 데뷔 날짜 (이후)
        debut_date_end (date): 데뷔 날짜 (이전)
    """

    name = dj_filters.CharFilter(lookup_expr="icontains")
    agency = dj_filters.CharFilter(lookup_expr="icontains")
    debut_date = dj_filters.DateFilter(lookup_expr="gte")
    debut_date_end = dj_filters.DateFilter(field_name="debut_date", lookup_expr="lte")

    class Meta:
        model = Idol
        fields = ["name", "agency", "debut_date", "debut_date_end"]


class IdolViewSet(ModelViewSet):
    """
    아이돌 정보 관리 뷰셋

    list:
    아이돌 목록 조회

    create:
    새 아이돌 생성

    retrieve:
    아이돌 상세 정보 조회

    update:
    아이돌 정보 전체 수정

    partial_update:
    아이돌 정보 부분 수정

    destroy:
    아이돌 정보 비활성화
    """

    queryset = Idol.objects.all()
    serializer_class = IdolSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = IdolFilter
    ordering_fields = ["debut_date", "name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        """기본적으로 활성화된 아이돌만 조회"""
        return Idol.objects.filter(is_active=True)

    def perform_create(self, serializer):
        """아이돌 생성 시 활성화 상태 True로 저장"""
        serializer.save(is_active=True)

    def perform_destroy(self, instance):
        """아이돌 삭제 대신 비활성화"""
        instance.deactivate()

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        """아이돌 활성화"""
        idol = self.get_object()
        idol.activate()
        return Response({"detail": "아이돌 정보가 활성화되었습니다."})

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """아이돌 비활성화"""
        idol = self.get_object()
        idol.deactivate()
        return Response({"detail": "아이돌 정보가 비활성화되었습니다."})


# class MemberViewSet(ModelViewSet):
#     """멤버 정보 관리 뷰셋"""
#     queryset = Member.objects.all()
#     serializer_class = MemberSerializer
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
#     filterset_fields = ['is_active']
#     ordering_fields = ['name', 'birth_date']
#     ordering = ['name']
#
#     def get_queryset(self):
#         """특정 아이돌의 멤버만 조회"""
#         idol_id = self.kwargs.get('idol_id')
#         return Member.objects.filter(idol_id=idol_id)
#
#     def perform_create(self, serializer):
#         """멤버 생성 시 아이돌 정보 추가"""
#         idol_id = self.kwargs.get('idol_id')
#         serializer.save(idol_id=idol_id)


# class ScheduleViewSet(ModelViewSet):
#     """일정 정보 관리 뷰셋"""
#     queryset = Schedule.objects.all()
#     serializer_class = ScheduleSerializer
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
#     filterset_fields = ['start_date', 'end_date']
#     ordering_fields = ['start_date', 'end_date']
#     ordering = ['start_date']
#
#     def get_queryset(self):
#         """특정 아이돌의 일정만 조회"""
#         idol_id = self.kwargs.get('idol_id')
#         return Schedule.objects.filter(idol_id=idol_id)
#
#     def perform_create(self, serializer):
#         """일정 생성 시 아이돌 정보 추가"""
#         idol_id = self.kwargs.get('idol_id')
#         serializer.save(idol_id=idol_id)


#
#
# class AlbumViewSet(ModelViewSet):
#     """앨범 정보 관리 뷰셋"""
#     queryset = Album.objects.all()
#     serializer_class = AlbumSerializer
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
#     filterset_fields = ['idol', 'release_date']
#     ordering_fields = ['release_date', 'title']
#     ordering = ['-release_date']

#
# class FanclubViewSet(ModelViewSet):
#     """팬클럽 정보 관리 뷰셋"""
#     queryset = Fanclub.objects.all()
#     serializer_class = FanclubSerializer
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]
#     filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
#     filterset_fields = ['idol']
#     ordering_fields = ['name']
#     ordering = ['name']
