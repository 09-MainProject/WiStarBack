from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PostViewSet

# API 버전
API_VERSION = 'v1'

# 1. router 만들기
router = DefaultRouter()

# 2. ViewSet 등록
# 게시물 관련 엔드포인트
router.register(r'posts', PostViewSet, basename='post')

# 3. 최종 URL 패턴
urlpatterns = [
    # API 버전을 포함한 URL 패턴
    path(f'api/{API_VERSION}/', include(router.urls)),

    # API 문서 URL (Swagger/OpenAPI)
    path('api/docs/', include('rest_framework.urls')),
]