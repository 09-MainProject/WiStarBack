from django_filters import rest_framework as dj_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.idol.docs import (
    idol_create_docs,
    idol_delete_docs,
    idol_list_docs,
    idol_retrieve_docs,
    idol_search_docs,
    idol_update_docs,
)
from apps.idol.models import Idol
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
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = IdolFilter
    ordering_fields = ["debut_date", "name", "created_at"]
    ordering = ["name"]

    def get_permissions(self):
        """
        각 액션에 따라 다른 권한 설정
        - list, retrieve: 모든 사용자 허용
        - 그 외: 인증된 사용자만 허용
        """
        if self.action in ["list", "retrieve"]:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """기본적으로 활성화된 아이돌만 조회"""
        return Idol.objects.filter(is_active=True)

    def perform_create(self, serializer):
        """아이돌 생성 시 활성화 상태 True로 저장"""
        serializer.save(is_active=True)

    @idol_list_docs
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @idol_create_docs
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @idol_retrieve_docs
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @idol_update_docs
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @idol_update_docs
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @idol_delete_docs
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.deactivate()
        return Response(
            {"detail": "아이돌 정보가 비활성화되었습니다."}, status=status.HTTP_200_OK
        )

    @idol_search_docs
    @action(detail=False, methods=['get'])
    def search(self, request):
        name = request.query_params.get('name', '')
        idols = self.get_queryset().filter(name__icontains=name)
        serializer = self.get_serializer(idols, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def activate(self, request):
        idol = self.get_object()
        idol.activate()
        return Response({"detail": "아이돌 정보가 활성화되었습니다."})

    @action(detail=True, methods=["post"])
    def deactivate(self, request):
        idol = self.get_object()
        idol.deactivate()
        return Response({"detail": "아이돌 정보가 비활성화되었습니다."})
