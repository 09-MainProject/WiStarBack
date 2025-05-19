from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PostViewSet

# 1. router 만들기
router = DefaultRouter(trailing_slash=False)

# 2. ViewSet 등록
# 게시물 관련 엔드포인트
router.register(r"", PostViewSet, basename="post")

# 3. 최종 URL 패턴
urlpatterns = [
    # 게시물 관련 엔드포인트
    path("posts", include(router.urls)),
    path(
        "posts/search",
        PostViewSet.as_view({"get": "posts_search"}),
        name="post-posts_search",
    ),
]
