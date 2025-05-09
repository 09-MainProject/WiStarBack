from django.urls import path

from apps import follow
from apps.follow.views import FollowCreateView, FollowDeleteView, FollowListView

app_name = "follow"


urlpatterns = [
    path("", FollowListView.as_view, name="follow"),
    path("{int:idol_id}/follow-status", FollowCreateView.as_view, name="follow"),
    path("{idol_id}/follows", FollowDeleteView.as_view, name="follow"),
]
