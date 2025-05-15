from django.urls import path

from .views import UserScheduleDetailView, UserScheduleListCreateView

urlpatterns = [
    path(
        "schedules",
        UserScheduleListCreateView.as_view(),
        name="user-schedule-list-create",
    ),
    path(
        "schedules/<int:pk>",
        UserScheduleDetailView.as_view(),
        name="user-schedule-detail",
    ),
]
