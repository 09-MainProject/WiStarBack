from django.urls import path

from .views import UserScheduleDetailView, UserScheduleListCreateView

urlpatterns = [
    path("", UserScheduleListCreateView.as_view(), name="user-schedule-list-create"),
    path("<int:pk>/", UserScheduleDetailView.as_view(), name="user-schedule-detail"),
]
