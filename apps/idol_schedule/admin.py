from django.contrib import admin
from .models import Schedule, Idol


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ["idol", "title", "location", "start_date", "end_date", "created_at"]
    list_filter = ["idol", "start_date"]
    search_fields = ["title", "description", "location"]
    autocomplete_fields = ["idol"]  # 아이돌이 많을 경우 유용

@admin.register(Idol)
class IdolAdmin(admin.ModelAdmin):
    list_display = ["name"]
    filter_horizontal = ["managers"]  # ManyToManyField를 수평 필터로 보여줌
    search_fields = ["name"]  # ✅ 추가: autocomplete_fields를 위한 필드