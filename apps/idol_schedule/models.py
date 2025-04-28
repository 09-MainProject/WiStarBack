from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class Idol(models.Model):
    name = models.CharField(max_length=100)
    managers = models.ManyToManyField(
        User, related_name="idols"
    )  # 매니저 다대다 관계 추가

    def __str__(self):
        return self.name

class Schedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="schedules")
    idol = models.ForeignKey(Idol, on_delete=models.CASCADE, related_name="schedules")
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255, default="미정")
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.idol.name}] {self.title}"

# 필드명	설명
# user	일정을 등록한 관리자 계정. User 모델과 연결
# idol	이 일정이 속한 아이돌
# title, description	일정 정보 텍스트
# start_date, end_date	일정 기간
# created_at	생성 시각 (자동 저장)
# updated_at	수정 시각 (업데이트마다 자동 갱신)