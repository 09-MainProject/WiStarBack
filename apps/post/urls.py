from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PostViewSet

# 1. router 만들기
router = DefaultRouter()

# 2. ViewSet 등록
# 게시물 관련 엔드포인트
router.register(r"posts", PostViewSet, basename="post")

# 3. 최종 URL 패턴
urlpatterns = [
    # 게시물 관련 엔드포인트
    path("", include(router.urls)),
    # 게시물 목록 조회 및 생성
    path('', PostListCreateView.as_view(), name='list-create'),

    # 특정 게시물 조회, 수정, 삭제
    path('<int:pk>/', PostRetrieveUpdateDestroyView.as_view(), name='detail'),

    # 게시물 조회수 증가
    path('<int:pk>/increase-views/', PostIncreaseViewsView.as_view(), name='increase-views'),

    # 작성자별 게시물 목록 조회
    path('author/<int:author_id>/', PostListByAuthorView.as_view(), name='list-by-author'),
]