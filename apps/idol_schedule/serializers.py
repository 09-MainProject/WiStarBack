from rest_framework import serializers

from .models import Idol, Schedule

class ScheduleSerializer(serializers.ModelSerializer):
    idol_name = serializers.CharField(source="idol.name", read_only=True)

    class Meta:
        model = Schedule
        fields = "__all__"
        read_only_fields = [
            "id",
            "user",
            "idol",
            "created_at",
            "updated_at",
            "idol_name",
        ]

    def validate(self, data):
        """
        일정의 시작일(start_date)이 종료일(end_date)보다 늦을 수 없도록 유효성 검사
        """
        start_date = data.get("start_date")
        end_date = data.get("end_date")

        # PATCH 요청일 경우, 기존 인스턴스 값을 반영해야 할 수 있음
        if self.instance:
            start_date = start_date or self.instance.start_date
            end_date = end_date or self.instance.end_date

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("시작일은 종료일보다 빨라야 합니다.")

        return data
