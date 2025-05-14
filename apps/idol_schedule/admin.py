from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Idol, Schedule

User = get_user_model()

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ["idol", "title", "location", "start_date", "end_date", "created_at"]
    list_filter = ["idol", "start_date"]
    search_fields = ["title", "description", "location"]
    autocomplete_fields = ["idol"]


@admin.register(Idol)
class IdolAdmin(admin.ModelAdmin):
    list_display = ["name"]
    filter_horizontal = ["managers"]
    search_fields = ["name"]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "managers":
            kwargs["queryset"] = User.objects.filter(is_staff=True)
        return super().formfield_for_manytomany(db_field, request, **kwargs)
