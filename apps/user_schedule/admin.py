# Register your models here.
from django.contrib import admin

from .models import UserSchedule  # 경로는 실제 위치에 따라 조정

admin.site.register(UserSchedule)
