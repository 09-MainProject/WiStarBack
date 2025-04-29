from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PostViewSet,
    PostListByAuthorView,
    CommentListCreateView,
    CommentRetrieveUpdateDestroyView
)

# 1. router 만들기
router = DefaultRouter()

# 2. ViewSet 등록
# 게시물 관련 엔드포인트
router.register(r'posts', PostViewSet, basename='post')

# 3. 최종 URL 패턴
urlpatterns = [
    # 게시물 관련 엔드포인트
    path('', include(router.urls)),
    
    # 작성자별 게시물 목록 조회
    path(
        'posts/author/<int:author_id>/',
        PostListByAuthorView.as_view(),
        name='post-list-by-author'
    ),
    
    # 댓글 관련 엔드포인트
    path(
        'posts/<int:post_id>/comments/',
        CommentListCreateView.as_view(),
        name='comment-list-create'
    ),
    path(
        'posts/<int:post_id>/comments/<int:pk>/',
        CommentRetrieveUpdateDestroyView.as_view(),
        name='comment-detail'
    ),
]