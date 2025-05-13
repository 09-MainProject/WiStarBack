from django.urls import path

from .views import LikeStatusView, LikeView

urlpatterns = [
    path(
        "",
        LikeView.as_view(),
        name="post-likes",
    ),
    path(
        "status/",
        LikeStatusView.as_view(),
        name="post-likes-status",
    ),
]
