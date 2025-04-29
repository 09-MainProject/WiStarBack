from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.idol.views import IdolViewSet
#, ScheduleViewSet

# API 버전
API_VERSION = 'v1'

# 1. router 만들기
router = DefaultRouter()

# 2. ViewSet 등록
# 아이돌 관련 엔드포인트
router.register(r'idols', IdolViewSet, basename='idol')

# # 멤버 관련 엔드포인트
# router.register(r'idols/(?P<idol_id>\d+)/members', MemberViewSet, basename='idol-member')

# # 일정 관련 엔드포인트
# router.register(r'idols/(?P<idol_id>\d+)/schedules', ScheduleViewSet, basename='idol-schedule')

# 3. 최종 URL 패턴
urlpatterns = [
    # API 버전을 포함한 URL 패턴
    path(f'api/{API_VERSION}/', include(router.urls)),

    # API 문서 URL (Swagger/OpenAPI)
    path('api/docs/', include('rest_framework.urls')),
]