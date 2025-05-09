# from datetime import datetime, timedelta
#
# from rest_framework import status
# from rest_framework.test import APITestCase
# from rest_framework_simplejwt.tokens import RefreshToken
#
# from apps.idol_schedule.models import Idol, Schedule
# from apps.user.models import User
#
#
# class ScheduleAPITestCase(APITestCase):
#     def setUp(self):
#         # 일반 유저 생성
#         self.user = User.objects.create_user(
#             email="user@example.com",
#             password="password123",
#             nickname="유저",
#             name="일반",
#         )
#         # 매니저 유저 생성 (is_staff=True)
#         self.manager = User.objects.create_user(
#             email="manager@example.com",
#             password="password123",
#             nickname="매니저",
#             name="관리자",
#             is_staff=True,
#         )
#         # 토큰 발급
#         self.manager_token = str(RefreshToken.for_user(self.manager).access_token)
#         self.user_token = str(RefreshToken.for_user(self.user).access_token)
#
#         # 아이돌 생성
#         self.idol = Idol.objects.create(name="Test Idol")
#
#         # 아이돌에 매니저 할당
#         self.idol.managers.add(self.manager)
#
#         # 기본 날짜 설정
#         self.start_date = datetime.now()
#         self.end_date = self.start_date + timedelta(days=1)
#
#         # Schedule 생성
#         self.schedule = Schedule.objects.create(
#             user=self.manager,
#             idol=self.idol,
#             title="스케줄 제목",
#             description="스케줄 설명",
#             location="서울",
#             start_date=self.start_date,
#             end_date=self.end_date,
#         )
#
#         self.base_url = f"/api/idols/{self.idol.id}/schedules/"
#
#     def auth(self, token):
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
#
#     def test_create_schedule_success(self):
#         self.auth(self.manager_token)  # 매니저로 인증
#         data = {
#             "title": "새 스케줄",
#             "description": "설명",
#             "location": "부산",
#             "start_date": self.start_date.isoformat(),
#             "end_date": self.end_date.isoformat(),
#         }
#         response = self.client.post(self.base_url, data)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(response.data["data"]["title"], data["title"])
#
#     def test_create_schedule_fail_not_manager(self):
#         self.auth(self.user_token)  # 일반 유저로 인증
#         data = {
#             "title": "권한 없음 스케줄",
#             "description": "설명",
#             "location": "대구",
#             "start_date": self.start_date.isoformat(),
#             "end_date": self.end_date.isoformat(),
#         }
#         response = self.client.post(self.base_url, data)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#
#     # 추가된 테스트
#     def test_create_schedule_with_valid_manager(self):
#         # 아이돌에 매니저를 할당한 후, 해당 매니저로 로그인하여 스케줄을 생성하는 테스트
#         client = self.client  # 기본 client 사용
#
#         # 로그인
#         self.auth(self.manager_token)
#
#         # 스케줄 데이터
#         data = {
#             "title": "새 일정",
#             "description": "일정 설명",
#             "start_date": "2025-05-01T00:00:00Z",
#             "end_date": "2025-05-02T00:00:00Z",
#             "location": "부산",
#         }
#
#         # 스케줄 생성 요청
#         response = client.post(self.base_url, data)
#
#         # 상태 코드와 응답 검증
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertIn("data", response.data)
#         self.assertEqual(response.data["data"]["title"], data["title"])
#         self.assertEqual(response.data["data"]["location"], data["location"])
