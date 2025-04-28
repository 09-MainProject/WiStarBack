from django.urls import path
from .views import PostListCreateView, PostRetrieveUpdateDestroyView, PostIncreaseViewsView, PostListByAuthorView

app_name = 'post'

urlpatterns = [
    # 게시물 목록 조회 및 생성
    path('', PostListCreateView.as_view(), name='list-create'),
    
    # 특정 게시물 조회, 수정, 삭제
    path('<int:pk>/', PostRetrieveUpdateDestroyView.as_view(), name='detail'),
    
    # 게시물 조회수 증가
    path('<int:pk>/increase-views/', PostIncreaseViewsView.as_view(), name='increase-views'),
    
    # 작성자별 게시물 목록 조회
    path('author/<int:author_id>/', PostListByAuthorView.as_view(), name='list-by-author'),
]