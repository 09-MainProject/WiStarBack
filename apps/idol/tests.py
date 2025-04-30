# from django.urls import reverse
# from rest_framework import status
# from rest_framework.test import APITestCase
# from django.contrib.auth import get_user_model
# from apps.idol.models import Idol
#
# User = get_user_model()
#
# class IdolTests(APITestCase):
#
#     def setUp(self):
#         self.user = User.objects.create_user(
#             username='testuser',
#             email='test@example.com',
#             password='testpass123'
#         )
#         self.client.force_authenticate(user=self.user)
#
#         self.idol = Idol.objects.create(
#             name="SHINee",
#             debut_date="2022-07-01",
#             agency="ADOR",
#             description="정말 코드란 멀까요",
#             profile_image="https://example.com/nj.jpg"
#         )
#
#     def test_idol_created(self):
#         self.assertEqual(self.idol.name, "SHINee")
