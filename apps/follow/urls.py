from django.urls import path

from apps import follow
from apps.follow.views import FollowCreateDestroyView, FollowListView, FollowStatusView

app_name = "follow"


urlpatterns = [
    path("follows", FollowListView.as_view(), name="follow_list"),
    path(
        "<int:idol_id>/follow-status",
        FollowStatusView.as_view(),
        name="follow_status",
    ),
    path(
        "<int:idol_id>/follows",
        FollowCreateDestroyView.as_view(),
        name="follow",
    ),
]
