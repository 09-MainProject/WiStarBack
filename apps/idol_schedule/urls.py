from django.urls import path

from .views import ScheduleListCreateView, ScheduleRetrieveUpdateDeleteView

app_name = "idol_schedule"

urlpatterns = [
    # 아이돌 ID를 URL에 포함시켜서 일정 목록을 조회하거나 생성
    path(
        "<int:idol_id>/schedules",
        ScheduleListCreateView.as_view(),
        name="schedule-list-create",
    ),
    # 특정 일정에 대해 조회, 수정, 삭제
    path(
        "<int:idol_id>/schedules/<int:pk>",
        ScheduleRetrieveUpdateDeleteView.as_view(),
        name="schedule-retrieve-update-delete",
    ),
]
