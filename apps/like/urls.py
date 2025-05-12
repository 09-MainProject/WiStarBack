from django.urls import path

from .views import LikeStatusView, LikeView

urlpatterns = [
    path(
        "posts/<int:post_id>/likes/",
        LikeView.as_view(),
        name="post-likes",
    ),
    path(
        "posts/<int:post_id>/likes/status/",
        LikeStatusView.as_view(),
        name="post-likes-status",
    ),
]
