from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet

router = DefaultRouter(trailing_slash=False)
router.register(r"", CommentViewSet, basename="comment")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "<int:pk>/like-status",
        CommentViewSet.as_view({"get": "like_status"}),
        name="comment-like-status",
    ),
]
