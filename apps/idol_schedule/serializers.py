from rest_framework import serializers

from .models import Idol, Schedule


# 실제사용
class ScheduleSerializer(serializers.ModelSerializer):
    idol_name = serializers.CharField(source="idol.name", read_only=True)

    class Meta:
        model = Schedule
        fields = "__all__"
        read_only_fields = ["id", "user", "created_at", "updated_at", "idol_name"]


# 테스트용
# class ScheduleSerializer(serializers.ModelSerializer):
#     idol = serializers.PrimaryKeyRelatedField(queryset=Idol.objects.all(), read_only=True)  # read_only로 설정
#
#     class Meta:
#         model = Schedule
#         fields = '__all__'