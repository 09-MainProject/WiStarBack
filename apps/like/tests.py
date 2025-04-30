from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from apps.post.models import Post
from .models import Like

User = get_user_model()


class TestLikeAPI(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.other_user = User.objects.create_user(
            username="otheruser", password="testpass"
        )
        self.post = Post.objects.create(
            title="테스트 게시글", content="내용", author=self.user
        )
        self.url_prefix = f"/api/post/{self.post.id}"

    def test_like_create(self):
        """좋아요 생성 테스트"""
        self.client.force_authenticate(user=self.user)
        url = f"{self.url_prefix}/likes"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            Like.objects.filter(
                type="post", object_id=self.post.id, user=self.user
            ).exists()
        )

    def test_like_duplicate(self):
        """중복 좋아요 방지 테스트"""
        self.client.force_authenticate(user=self.user)
        url = f"{self.url_prefix}/likes"
        self.client.post(url)
        response = self.client.post(url)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT],
        )

    def test_like_delete(self):
        """좋아요 삭제 테스트"""
        self.client.force_authenticate(user=self.user)
        like = Like.objects.create(type="post", object_id=self.post.id, user=self.user)
        url = f"{self.url_prefix}/likes/{like.id}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Like.objects.filter(id=like.id).exists())

    def test_like_status(self):
        """좋아요 여부 확인 테스트"""
        self.client.force_authenticate(user=self.user)
        url = f"{self.url_prefix}/like-status"
        # 좋아요 누르기 전
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["liked"])
        # 좋아요 누른 후
        Like.objects.create(type="post", object_id=self.post.id, user=self.user)
        response = self.client.get(url)
        self.assertTrue(response.data["liked"])

    def test_like_list(self):
        """좋아요 목록 조회 테스트"""
        self.client.force_authenticate(user=self.user)
        Like.objects.create(type="post", object_id=self.post.id, user=self.user)
        Like.objects.create(type="post", object_id=self.post.id, user=self.other_user)
        url = f"{self.url_prefix}/likes"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)

    def test_like_requires_auth(self):
        """비로그인 사용자는 좋아요 기능을 사용할 수 없음"""
        url = f"{self.url_prefix}/likes"
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        like = Like.objects.create(type="post", object_id=self.post.id, user=self.user)
        url = f"{self.url_prefix}/likes/{like.id}"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        url = f"{self.url_prefix}/like-status"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
