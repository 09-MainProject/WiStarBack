from rest_framework import serializers
from rest_framework import generics, permissions, status, filters
from django_filters.rest_framework import DjangoFilterBackend
# from apps.idol.models import Idol, Member, Album, Schedule, Fanclub
# from apps.idol.serializers import IdolSerializer
# MemberSerializer, AlbumSerializer, ScheduleSerializer, \
#     FanclubSerializer
import django_filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.viewsets import ModelViewSet
from apps.idol.models import Idol


class IdolFilter(django_filters.FilterSet):
    """
    아이돌 검색 필터

    Attributes:
        name (str): 아이돌 이름 (부분 일치)
        agency (str): 소속사 (부분 일치)
        debut_date (date): 데뷔 날짜 (이후)
        debut_date_end (date): 데뷔 날짜 (이전)
    """
    name = django_filters.CharFilter(lookup_expr='icontains')
    agency = django_filters.CharFilter(lookup_expr='icontains')
    debut_date = django_filters.DateFilter(lookup_expr='gte')
    debut_date_end = django_filters.DateFilter(field_name='debut_date', lookup_expr='lte')

    class Meta:
        model = Idol
        fields = ['name', 'agency', 'debut_date', 'debut_date_end']


class IdolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Idol
        fields = 'all'