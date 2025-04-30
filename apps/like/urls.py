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
    path("<str:type>/<int:id>/like-status", like_status, name="like-status"),
    path("<str:type>/<int:id>/likes", like_list, name="like-list"),
    path("<str:type>/<int:id>/likes/<int:pk>", like_detail, name="like-detail"),
]
