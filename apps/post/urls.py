from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PostLikeView, PostViewSet

# 1. router 만들기
router = DefaultRouter()

# 2. ViewSet 등록
# 게시물 관련 엔드포인트
router.register(r"", PostViewSet, basename="post")

# 3. 최종 URL 패턴
urlpatterns = [
    # 게시물 관련 엔드포인트
    path("", include(router.urls)),
    path("<int:pk>/like/", PostLikeView.as_view(), name="post-like"),
]
