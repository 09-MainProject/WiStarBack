from django.urls import path

from .views import LikeViewSet

like_list = LikeViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)
like_detail = LikeViewSet.as_view(
    {
        "delete": "destroy",
    }
)
like_status = LikeViewSet.as_view(
    {
        "get": "like_status",
    }
)

urlpatterns = [
    path(
        "<str:app_label>/<int:object_id>/like-status",
        like_status,
        name="like-status",
    ),
    path(
        "<str:app_label>/<int:object_id>/likes",
        like_list,
        name="like-list"
    ),
    path(
        "<str:app_label>/<int:object_id>/likes/<int:pk>",
        like_detail,
        name="like-detail",
    ),
]
