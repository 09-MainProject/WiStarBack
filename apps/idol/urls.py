from django.urls import path

from .views import IdolViewSet

app_name = "idols"

urlpatterns = [
    path("", IdolViewSet.as_view({"get": "list", "post": "create"}), name="idol-list"),
    path(
        "<int:pk>/",
        IdolViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="idol-detail",
    ),
    path(
        "<int:pk>/activate/",
        IdolViewSet.as_view({"post": "activate"}),
        name="idol-activate",
    ),
    path(
        "<int:pk>/deactivate/",
        IdolViewSet.as_view({"post": "deactivate"}),
        name="idol-deactivate",
    ),
]
