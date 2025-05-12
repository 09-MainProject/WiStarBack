from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.like.models import Like
from apps.post.models import Post

User = get_user_model()


class LikeTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@test.com", password="test1234", name="테스터", nickname="tester"
        )
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(
            title="테스트 게시글", content="내용입니다.", author=self.user
        )

    def test_create_like(self):
        url = reverse("post-likes", kwargs={"post_id": self.post.id})
        response = self.client.post(url)
        self.assertIn(response.status_code, [200, 201])

    def test_create_like_unauthenticated(self):
        self.client.force_authenticate(user=None)
        url = reverse("post-likes", kwargs={"post_id": self.post.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

    def test_delete_like(self):
        url = reverse("post-likes", kwargs={"post_id": self.post.id})
        self.client.post(url)  # 먼저 좋아요 생성
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)

    def test_delete_like_unauthorized(self):
        url = reverse("post-likes", kwargs={"post_id": self.post.id})
        self.client.post(url)
        other_user = User.objects.create_user(
            email="other@test.com",
            password="test1234",
            name="다른유저",
            nickname="other",
        )
        self.client.force_authenticate(user=other_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

    def test_list_likes(self):
        url = reverse("post-likes", kwargs={"post_id": self.post.id})
        self.client.post(url)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)

    def test_like_status(self):
        url = reverse("post-likes-status", kwargs={"post_id": self.post.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
