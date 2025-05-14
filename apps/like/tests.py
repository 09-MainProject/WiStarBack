from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.like.models import Like
from apps.post.models import Post
from apps.comment.models import Comment

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
        self.comment = Comment.objects.create(
            post=self.post, author=self.user, content="댓글입니다."
        )

    def test_post_like_status(self):
        url = f"/api/posts/{self.post.id}/like-status"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertIn("liked", response.data["data"])
        self.assertFalse(response.data["data"]["liked"])
        # 좋아요 생성 후 상태 확인
        self.client.post(f"/api/posts/{self.post.id}/likes/")
        response = self.client.get(url)
        self.assertTrue(response.data["data"]["liked"])

    def test_comment_like_status(self):
        url = f"/api/comments/{self.comment.id}/like-status"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.data)
        self.assertIn("liked", response.data["data"])
        self.assertFalse(response.data["data"]["liked"])
        # 좋아요 생성 후 상태 확인
        self.client.post(f"/api/comments/{self.comment.id}/likes/")
        response = self.client.get(url)
        self.assertTrue(response.data["data"]["liked"])

    def test_post_like_create_and_delete(self):
        url = f"/api/posts/{self.post.id}/likes/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Like.objects.filter(object_id=self.post.id).exists())
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Like.objects.filter(object_id=self.post.id).exists())

    def test_comment_like_create_and_delete(self):
        url = f"/api/comments/{self.comment.id}/likes/"
        response = self.client.post(url)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Like.objects.filter(object_id=self.comment.id).exists())
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Like.objects.filter(object_id=self.comment.id).exists())
