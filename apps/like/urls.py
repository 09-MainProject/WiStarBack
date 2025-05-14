from django.urls import path

from .views import LikeStatusView, LikeView

app_name = "like"

urlpatterns = [
    # 게시글 좋아요
    path(
        "posts/<int:id>/likes/",
        LikeView.as_view(),
        name="post-likes",
    ),
    # 댓글 좋아요
    path(
        "comments/<int:id>/likes/",
        LikeView.as_view(),
        name="comment-likes",
    ),
    # 통합 좋아요 상태 조회
    path(
        "<str:type>/<int:id>/like-status",
        LikeStatusView.as_view(),
        name="like-status",
    ),
]
